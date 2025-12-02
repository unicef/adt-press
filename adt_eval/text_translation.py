"""Translation evaluation implementation.

"""
import json
from pathlib import Path
from typing import Any, Dict, TypedDict, List, Optional, Literal, Union


import pandas as pd
import ast
import mlflow
import logging
from label_studio_sdk import LabelStudio
from mlflow.entities import Feedback
from mlflow.genai import scorer
from mlflow.genai.datasets import get_dataset
from litellm import completion

from adt_eval.base import BaseEvaluator
from adt_eval.utils.file import _encode_image_to_base64
from adt_eval.prompts import TRANSLATION_SCORER_SYSTEM_PROMPT
from adt_eval.schema import TranslationEvalOutput

from adt_press.llm.text_extraction import get_page_text
from adt_press.models.pdf import Page
from adt_press.llm.text_translation import get_text_translation
from adt_press.models.config import PromptConfig

logging.getLogger("LiteLLM").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)

@scorer  
def is_acceptable_translation(inputs: dict, outputs: dict) -> Feedback:
    "This returns the translation of the original text"

    input_text_dict = inputs.get("input_text")

    if type(input_text_dict) == str:
        input_text_dict = ast.literal_eval(input_text_dict)

    input_text = input_text_dict.get("text")
    source_language_code  = outputs.get("input_language")
    
    output_text = outputs.get("text")
    target_language_code  = outputs.get("output_language")

    image_path = input_text_dict.get("image_path")

    image_b64 = _encode_image_to_base64(image_path)

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

    response = json.loads(eval_output.model_dump()["choices"][0]["message"]["content"])

    return Feedback(
        name="is_acceptable_translation",
        value=response["is_translation_acceptable"],
        rationale=response["rationale"],
    )

class TextTranslationEvaluator(BaseEvaluator):
    """Evaluator for translation accuracy."""

    def __init__(self, global_config: Dict[str, Any], task_config: Dict[str, Any], output_dir: Path):
        super().__init__(global_config, task_config, output_dir)

        self.optimizer_prompt_config = None
        self.optimization_traces_df = None
        self.prompt_analysis_job_order = None
        self.metric_calculators = {}
        self.metric_name = None
        self.metric_threshold = None

        self.translation_cfg = {}
        self.translation_cfg['input_language'] = self.experiment_run_cfg.get("input_language")
        self.translation_cfg['output_language'] = self.experiment_run_cfg.get("output_language")

    def process_case(self, step: int, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single test case."""
        pass

    def load_prompt_analysis_job_order(self):

        logging.info("Loading prompt analysis job order...")

        #load best run by metric
        logging.info("Loading best run by metric...")
        self.metric_name = self.optimization_cfg.get("metric_name")
        self.metric_threshold = self.optimization_cfg.get("metric_threshold")
        best_run_dict = self.mlflow_tool.get_best_run_by_metric(self.experiment_run_cfg["experiment_id"], self.metric_name)
        self.best_run_info = best_run_dict

        metric = f"metrics.{self.optimization_cfg['metric_name']}/mean"
        
        logging.info(f"Loaded the best run: '{self.best_run_info['tags.mlflow.runName']}' with the metrics: {metric} = {self.best_run_info[metric]}")
        
        if best_run_dict is None:
            raise ValueError("No best run found for metric: %s" % self.metric_name)

        #load best run prompt
        logging.info("Loading best run prompt...")
        self.optimizer_prompt_config = PromptConfig(
            model=best_run_dict["tags.model_name"],
            template_path=best_run_dict["tags.prompt_uri"],
            examples=[],
        )
        
        #load best run prompt
        best_run_prompt = mlflow.genai.load_prompt(best_run_dict["tags.prompt_uri"])
        optimizer_prompt_template = best_run_prompt.template

        #load the traces that need to be used to optimize the prompt
        logging.info("Loading traces...")
        traces_df = self.mlflow_tool.get_traces(best_run_dict['run_id'])
        assessment_traces_df = self.mlflow_tool.get_assessments(traces_df)

        optimization_traces_df = assessment_traces_df[(assessment_traces_df['assessment_name'] == self.metric_name) & 
                                                      (assessment_traces_df['metric_value'] < self.metric_threshold)]
        self.optimization_traces_df = optimization_traces_df

        if optimization_traces_df.empty:
            raise ValueError("No optimization traces found")
               
        #get optimization cases
        logging.info("Loading optimization cases...")
        cases = []
        count = 1
        for index, row in optimization_traces_df.iterrows():
            case = {}
            case['case_no'] = count
            case['request'] = row['request']
            case['response'] = row['response']
            case['reason_why_metric_requires_optimization'] = row['rationale'] if pd.notna(row['rationale']) else "value needs to be improved"
            cases.append(case)
            count += 1

        prompt_analysis_job_order = {
            "prompt_name": best_run_prompt.name, #this will be used to create subsequent prompt versions
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
        text_id = input_text_dict['text_id']
        text_type = input_text_dict['text_type']
        text = input_text_dict['text']
        page_image_local_path = input_text_dict['page_image_local_path']
        input_language = self.translation_cfg['input_language']
        output_language = self.translation_cfg['output_language']

        coro = get_text_translation(
            self.experiment_run_prompt['config'],
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
        """Prepare data for evaluation."""
        if self.dataset_cfg['is_label_studio_dataset']:
            records = []
            step= 1
            for entry in data:
                annotations = entry["annotations"][0]["result"]
                page_image = entry["data"]['page_image']

                text_no = 1
                for annotation in annotations:
                    if annotation["from_name"] == "notes":
                        continue

                    text_id = text_no
                    text = annotation['value']['text']
                    text_type = annotation['value']['taxonomy'][0][0]
                    records.append(
                        {
                            "inputs": {
                                "input_text": str({
                                    "text_id": str(text_id), 
                                    "text_type": text_type, 
                                    "text": text,
                                    "page_image": page_image,
                                    "step": str(step),
                                    "input_language": self.translation_cfg['input_language'], 
                                    "output_language": self.translation_cfg['output_language'],
                                })
                            },
                            "expectations": {},
                            "step": str(step),
                            "entry_id": entry["id"],
                        }
                    )
                    text_no += 1
                step += 1    
            
            return records
        else:

            pass

    def get_report_results_and_metrics(self):
        """Get report results and metrics."""

        #get step
        def _get_step(row):
            try:
                if type(row["request"]["input_text"]) == str:
                    input_text = ast.literal_eval(row["request"]["input_text"])
                else:
                    input_text = row["request"]["input_text"]
            except (ValueError, SyntaxError) as exc:
                logging.warning(
                    "Skipping record %s due to invalid input_text: %s",
                    row.get("entry_id"),
                    exc,
                )
                return None
            return input_text.get("step")

        #preparing the code to do the template renderring
        def _calculate_results(df):
            results = []
            count = 1
            translations =[]

            for step in df["step"].unique():
                step_df = df[df["step"] == step]
                for _, row in step_df.iterrows():

                    text = row["response"]['original_text']
                    translation = row["response"]['text']
                    is_acceptable_translation = row['is_acceptable_translation/value']
                    step = row["step"]
                    score = round(step_df['is_acceptable_translation/value'].sum()/len(step_df), 2)

                    #get image relative path
                    page_image_path = row["response"]['page_image_path'].replace(str(self.output_dir) + "/", "")

                    translations.append({
                        "original_text": text,
                        "translation": translation,
                        "is_acceptable_translation": is_acceptable_translation
                        
                    })

                    count += 1
                    #if count %10 == 0:
                    result = {
                        "score": score,
                        "score_count": 0,
                        "step": step,
                        "translations": translations,
                        "page_image_path": page_image_path,
                    }

                results.append(result)
                translations =[]

            return results

        #calculate the results
        result_df = self.experiment_run_results.result_df.copy()
        result_df['step'] = result_df.apply(_get_step, axis=1)
        result_df.sort_values(by='step', inplace=True)
        results = _calculate_results(result_df)

        #calculate metrics
        metrics = {
            key.replace("/mean", ""): round(float(value), 3)
            for key, value in self.experiment_run_results.metrics.items()
        }

        metrics['score'] = metrics['is_acceptable_translation']
        return results, metrics
            
    def execute_eval_experiment_run(self, optimized_prompt_uri: str = None):
        """Execute the eval experiment run."""

        EXPERIMENT_RUN_NAME = "adt-translation-run-" + pd.Timestamp.now(tz="Europe/Madrid").strftime("%Y%m%d-%H%M%S")

        #get dataset
        dataset = get_dataset(dataset_id=self.dataset_cfg["dataset_id"])

        #get prompt
        if optimized_prompt_uri is None:
            self.experiment_run_prompt['uri'] = mlflow.genai.load_prompt(self.prompt_cfg["prompt_uri"]).uri
        else:
            self.experiment_run_prompt['uri'] = optimized_prompt_uri

        prompt_config_dict = {
                    "model": self.experiment_run_cfg["model"],
                    "template_path": self.experiment_run_prompt['uri'],
                    "source": "mlflow",
                    "examples": []
                }

        self.experiment_run_prompt['config'] = PromptConfig(**prompt_config_dict)

        logging.info("Running experiment run '%s' with prompt: %s", EXPERIMENT_RUN_NAME, self.experiment_run_prompt['uri'])

        with mlflow.start_run(run_name=EXPERIMENT_RUN_NAME):
            # Helpful tags for filtering in UI
            mlflow.set_tag("prompt_uri", self.experiment_run_prompt['uri'])
            mlflow.set_tag("dataset_id", self.dataset_cfg["dataset_id"])
            mlflow.set_tag("model_name", self.experiment_run_prompt['config'].model)

            # Log the model + prompt association
            mlflow.openai.log_model(
                model=self.experiment_run_prompt['config'].model,
                prompts=[self.experiment_run_prompt['uri']],
                task="chat.completions",
            )

            results = mlflow.genai.evaluate(
                data=dataset,
                predict_fn=self.predict_ftn,
                scorers=[is_acceptable_translation],
            )

            self.experiment_run_results = results

        logging.info("Evaluation completed. Metrics: %s", results.metrics)
        return self.experiment_run_results
