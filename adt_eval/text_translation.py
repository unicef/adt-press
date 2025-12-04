# text_translation.py
"""Translation evaluation implementation."""

import ast
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import mlflow
import pandas as pd
from litellm import completion
from mlflow.entities import Feedback
from mlflow.genai import scorer
from mlflow.genai.datasets import get_dataset

from adt_eval.base import BaseEvaluator
from adt_eval.prompts import TRANSLATION_SCORER_SYSTEM_PROMPT
from adt_eval.schema import TranslationEvalOutput
from adt_eval.utils.file import _encode_image_to_base64
from adt_press.llm.text_translation import get_text_translation
from adt_press.models.config import PromptConfig

# Use module-level logger instead of reconfiguring logging
logging.getLogger("LiteLLM").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@scorer
def is_acceptable_translation(inputs: Dict[str, Any], outputs: Dict[str, Any]) -> Feedback:
    """Score whether a translation is acceptable or not, based on an LLM judge."""

    input_text_dict = inputs.get("input_text")

    if isinstance(input_text_dict, str):
        input_text_dict = ast.literal_eval(input_text_dict)

    input_text_dict = input_text_dict or {}

    input_text = input_text_dict.get("text")
    source_language_code = outputs.get("input_language")

    output_text = outputs.get("text")
    target_language_code = outputs.get("output_language")

    # Prefer the page image path from the model outputs, which is set in predict_ftn
    image_path = outputs.get("page_image_path")

    image_b64 = _encode_image_to_base64(image_path) if image_path else None

    if image_b64:
        user_content = [
            {
                "type": "text",
                "text": (
                    "Evaluate whether the following Translation is ACCEPTABLE, "
                    "using the criteria in the system prompt.\n\n"
                    f"source_language_code: {source_language_code}\n"
                    f"input_text :\n{input_text}\n\n"
                    f"target_language_code: {target_language_code}\n"
                    f"output_text :\n{output_text}\n\n"
                    "Below is the textbook page image in base64 format. "
                    "Use it only to understand the context and how the text is used:\n"
                ),
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_b64}"
                },
            },
        ]
    else:
        user_content = (
            "Evaluate whether the following Translation is ACCEPTABLE, "
            "using the criteria in the system prompt.\n\n"
            f"source_language_code: {source_language_code}\n"
            f"input_text :\n{input_text}\n\n"
            f"target_language_code: {target_language_code}\n"
            f"output_text :\n{output_text}\n\n"
        )

    messages = [
        {"role": "system", "content": TRANSLATION_SCORER_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    eval_output = completion(
        model="gpt-5",
        messages=messages,
        response_format=TranslationEvalOutput,
    )

    # Align with how you're handling other response_format=Pydantic calls
    msg = eval_output.choices[0].message
    translation_eval = TranslationEvalOutput.model_validate_json(msg.content)

    return Feedback(
        name="is_acceptable_translation",
        value=translation_eval.is_translation_acceptable,
        rationale=translation_eval.rationale,
    )


class TextTranslationEvaluator(BaseEvaluator):
    """Evaluator for translation accuracy."""

    def __init__(self, global_config: Dict[str, Any], task_config: Dict[str, Any], output_dir: Path):
        super().__init__(global_config, task_config, output_dir)

        self.optimizer_prompt_config = None
        self.optimization_traces_df = None
        self.prompt_analysis_job_order = None
        self.metric_calculators: Dict[str, Any] = {}
        self.metric_name: str | None = None
        self.metric_threshold: float | None = None

        self.translation_cfg: Dict[str, Any] = {}
        self.translation_cfg["input_language"] = self.experiment_run_cfg.get("input_language")
        self.translation_cfg["output_language"] = self.experiment_run_cfg.get("output_language")

    async def process_case(self, step: int, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single test case (not used in this evaluator)."""
        raise NotImplementedError("TextTranslationEvaluator does not implement process_case for async workflows.")

    def load_prompt_analysis_job_order(self):
        logger.info("Loading prompt analysis job order...")

        # load best run by metric
        logger.info("Loading best run by metric...")
        self.metric_name = self.optimization_cfg.get("metric_name")
        self.metric_threshold = self.optimization_cfg.get("metric_threshold")
        best_run_dict = self.mlflow_tool.get_best_run_by_metric(
            self.experiment_run_cfg["experiment_id"],
            self.metric_name,
        )
        self.best_run_info = best_run_dict

        if best_run_dict is None:
            raise ValueError(f"No best run found for metric: {self.metric_name}")

        metric = f"metrics.{self.optimization_cfg['metric_name']}/mean"
        logger.info(
            "Loaded the best run: '%s' with the metrics: %s = %s",
            self.best_run_info["tags.mlflow.runName"],
            metric,
            self.best_run_info[metric],
        )

        # load best run prompt
        logger.info("Loading best run prompt...")
        self.optimizer_prompt_config = PromptConfig(
            model=best_run_dict["tags.model_name"],
            template_path=best_run_dict["tags.prompt_uri"],
            examples=[],
        )

        best_run_prompt = mlflow.genai.load_prompt(best_run_dict["tags.prompt_uri"])
        optimizer_prompt_template = best_run_prompt.template

        # load the traces that need to be used to optimize the prompt
        logger.info("Loading traces...")
        traces_df = self.mlflow_tool.get_traces(best_run_dict["run_id"])
        assessment_traces_df = self.mlflow_tool.get_assessments(traces_df)

        optimization_traces_df = assessment_traces_df[
            (assessment_traces_df["assessment_name"] == self.metric_name)
            & (assessment_traces_df["metric_value"] < self.metric_threshold)
        ]
        self.optimization_traces_df = optimization_traces_df

        if optimization_traces_df.empty:
            raise ValueError("No optimization traces found")

        # get optimization cases
        logger.info("Loading optimization cases...")
        cases: List[Dict[str, Any]] = []
        count = 1
        for _, row in optimization_traces_df.iterrows():
            case = {
                "case_no": count,
                "request": row["request"],
                "response": row["response"],
                "reason_why_metric_requires_optimization": (
                    row["rationale"] if pd.notna(row["rationale"]) else "value needs to be improved"
                ),
            }
            cases.append(case)
            count += 1

        prompt_analysis_job_order = {
            "prompt_name": best_run_prompt.name,  # this will be used to create subsequent prompt versions
            "prompt_template": optimizer_prompt_template,
            "cases_that_require_optimization": cases,
        }

        self.prompt_analysis_job_order = prompt_analysis_job_order
        return self.prompt_analysis_job_order

    def predict_ftn(self, input_text: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for text translation + LaBSE scoring.
        """

        input_text_dict = ast.literal_eval(input_text)
        text_id = input_text_dict["text_id"]
        text_type = input_text_dict["text_type"]
        text = input_text_dict["text"]
        page_image_local_path = input_text_dict["page_image_local_path"]
        input_language = self.translation_cfg["input_language"]
        output_language = self.translation_cfg["output_language"]

        coro = get_text_translation(
            self.experiment_run_prompt["config"],
            [(text_id, text_type, text)],
            input_language,
            output_language,
        )

        response = self._run_coro(coro)
        response_dict = response[0].model_dump()
        response_dict["original_text"] = text
        response_dict["input_language"] = input_language
        response_dict["output_language"] = output_language
        response_dict["page_image_path"] = page_image_local_path

        return response_dict

    def create_eval_dataset_records(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare data for evaluation in the format required the MLFLow Eval (https://mlflow.org/docs/latest/genai/eval-monitor) """
        if self.dataset_cfg["is_label_studio_dataset"]:
            records: List[Dict[str, Any]] = []
            step = 1
            for entry in data:
                annotations = entry["annotations"][0]["result"]
                page_image = entry["data"]["page_image"]

                text_no = 1
                for annotation in annotations:
                    if annotation["from_name"] == "notes":
                        continue

                    text_id = text_no
                    text = annotation["value"]["text"]
                    text_type = annotation["value"]["taxonomy"][0][0]
                    records.append(
                        {
                            "inputs": {
                                "input_text": str(
                                    {
                                        "text_id": str(text_id),
                                        "text_type": text_type,
                                        "text": text,
                                        "page_image": page_image,
                                        "step": str(step),
                                        "input_language": self.translation_cfg["input_language"],
                                        "output_language": self.translation_cfg["output_language"],
                                    }
                                )
                            },
                            "expectations": {},
                            "step": str(step),
                            "entry_id": entry["id"],
                        }
                    )
                    text_no += 1
                step += 1

            return records

        # Future: support non-Label Studio datasets
        raise NotImplementedError("Non–Label Studio datasets are not yet supported in TextTranslationEvaluator.")

    def get_report_results_and_metrics(self):
        """Get report results and metrics."""

        def _get_step(row: Dict[str, Any]):
            try:
                if isinstance(row["request"]["input_text"], str):
                    input_text = ast.literal_eval(row["request"]["input_text"])
                else:
                    input_text = row["request"]["input_text"]
            except (ValueError, SyntaxError) as exc:
                logger.warning(
                    "Skipping record %s due to invalid input_text: %s",
                    row.get("entry_id"),
                    exc,
                )
                return None
            return input_text.get("step")

        def _calculate_results(df: pd.DataFrame) -> List[Dict[str, Any]]:
            results: List[Dict[str, Any]] = []

            for step_value in df["step"].unique():
                step_df = df[df["step"] == step_value]
                translations: List[Dict[str, Any]] = []

                score = round(step_df["is_acceptable_translation/value"].sum() / len(step_df), 2)

                result: Dict[str, Any] | None = None
                for _, row in step_df.iterrows():
                    text = row["response"]["original_text"]
                    translation = row["response"]["text"]
                    is_acceptable_translation = row["is_acceptable_translation/value"]
                    page_image_path = row["response"]["page_image_path"].replace(
                        f"{self.output_dir}/", ""
                    )

                    translations.append(
                        {
                            "original_text": text,
                            "translation": translation,
                            "is_acceptable_translation": is_acceptable_translation,
                        }
                    )

                    result = {
                        "score": score,
                        "score_count": 0,
                        "step": step_value,
                        "translations": translations,
                        "page_image_path": page_image_path,
                    }

                if result is not None:
                    results.append(result)

            return results

        result_df = self.experiment_run_results.result_df.copy()
        result_df["step"] = result_df.apply(_get_step, axis=1)
        result_df.sort_values(by="step", inplace=True)
        results = _calculate_results(result_df)

        metrics = {
            key.replace("/mean", ""): round(float(value), 3)
            for key, value in self.experiment_run_results.metrics.items()
        }

        metrics["score"] = metrics["is_acceptable_translation"]
        return results, metrics

    def execute_eval_experiment_run(self, optimized_prompt_uri: str | None = None):
        """Execute the eval experiment run."""

        experiment_run_name = (
            "adt-translation-run-"
            + pd.Timestamp.now(tz="Europe/Madrid").strftime("%Y%m%d-%H%M%S")
        )

        # get dataset
        dataset = get_dataset(dataset_id=self.dataset_cfg["dataset_id"])

        # get prompt
        if optimized_prompt_uri is None:
            self.experiment_run_prompt["uri"] = mlflow.genai.load_prompt(
                self.prompt_cfg["prompt_uri"]
            ).uri
        else:
            self.experiment_run_prompt["uri"] = optimized_prompt_uri

        prompt_config_dict = {
            "model": self.experiment_run_cfg["model"],
            "template_path": self.experiment_run_prompt["uri"],
            "source": "mlflow",
            "examples": [],
        }

        self.experiment_run_prompt["config"] = PromptConfig(**prompt_config_dict)

        logger.info(
            "Running experiment run '%s' with prompt: %s",
            experiment_run_name,
            self.experiment_run_prompt["uri"],
        )

        with mlflow.start_run(run_name=experiment_run_name):
            # Helpful tags for filtering in UI
            mlflow.set_tag("prompt_uri", self.experiment_run_prompt["uri"])
            mlflow.set_tag("dataset_id", self.dataset_cfg["dataset_id"])
            mlflow.set_tag("model_name", self.experiment_run_prompt["config"].model)

            # Log the model + prompt association
            mlflow.openai.log_model(
                model=self.experiment_run_prompt["config"].model,
                prompts=[self.experiment_run_prompt["uri"]],
                task="chat.completions",
            )

            results = mlflow.genai.evaluate(
                data=dataset,
                predict_fn=self.predict_ftn,
                scorers=[is_acceptable_translation],
            )

            self.experiment_run_results = results

        logger.info("Evaluation successfully completed!")
        return self.experiment_run_results
