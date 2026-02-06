"""Text type evaluation implementation.

Some notes on the scoring of matches:
- The LabelStudio text_type dataset sometimes had errors in the text_transcript that were later corrected. Thus, in this script, we correct some of these errors as well (for example, removing double spaces).
- Mismatches are often introduced by mismatched directional quotations, e.g. ’,”,‘,“. These are replaced by non-directional quotations in both the LLM output and the Gold Standard.
- The match strategy implemented is a greedy one.
    - For each line in the LLM output, a list of labels is created (where each item in the list is the text type corresponding to one repetition of the line in the LLM output).
    - For each line in the Gold Standard transcript, we seek a match and, if the line matches, one text type item is 'used up' from the list.
"""

import ast
import os
import traceback
from pathlib import Path
from typing import Any, Dict, List

from banks import Prompt
from litellm import completion
from mlflow.entities import Feedback
from mlflow.genai import scorer

from adt_eval.mlflow_base import MLflowEvaluatorBase
from adt_eval.utils.file import encode_image_to_base64, load_json, save_json
from adt_eval.utils.text_translation import build_eval_translations, build_eval_translations_with_scores
from adt_press.llm.text_translation import get_text_translation
from adt_press.models.eval.text_translation import TranslationEvalOutputs
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.languages import Language


@scorer
def is_acceptable_translation(inputs: Dict[str, Any], outputs: Dict[str, Any]) -> Feedback:
    base_language = inputs.get("base_language", "en")
    target_language = inputs.get("target_language", "es")
    judge_cfg = (inputs.get("scorers") or {}).get("translation_acceptability") or {}
    eval_page_text_translations = outputs.get("eval_page_text_translations", [])

    try:
        # convert Language objects to dictionaries
        base_language = base_language.model_dump()
        target_language = target_language.model_dump()

        # get image base64
        image_path = inputs.get("image_path") or inputs.get("page_image_path") or ""
        image_b64 = encode_image_to_base64(image_path)

        #build context
        context = dict(
            base_language=base_language,
            target_language=target_language,
            eval_page_text_translations=eval_page_text_translations,
            image_data_url=f"data:image/png;base64,{image_b64}" if image_b64 else None,
        )

        prompt_path = judge_cfg.get("prompt_path") or "prompts/eval/text_translation_eval.jinja2"
        prompt = Prompt(cached_read_text_file(prompt_path))

        eval_output = completion(
                model=judge_cfg.get("llm_as_judge_model") or "gpt-5",
                messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
                response_format=TranslationEvalOutputs,
            )

        msg = eval_output.choices[0].message
        translation_eval = TranslationEvalOutputs.model_validate_json(msg.content)
        translation_output = translation_eval.model_dump()["outputs"]

        #calculating the translation eval summary
        summary_of_translations = [translation['is_translation_acceptable'] for translation in translation_output]
        summary_of_translations_metadata = [
            {"text_id": translation["text_id"], 
            "is_translation_acceptable": translation["is_translation_acceptable"],
            "rationale": translation["rationale"]} 
            for translation in translation_output]
        summary_of_failed_translations = [
            {"text_id": translation["text_id"], "rationale": translation["rationale"]}
            for translation in translation_output
            if not translation["is_translation_acceptable"]
        ]

        #calculating the translation eval metric
        metric= round(sum(summary_of_translations) / len(summary_of_translations), 2)
        
        #calculating the combined translation eval rationale
        if summary_of_failed_translations:
            combined_rationale = "The folowing translations are not acceptable:\n\n"
            for entry in summary_of_failed_translations:
                combined_rationale += f"- text_id: {entry['text_id']}\n  reason: {entry['rationale']}\n\n" 
        else:
            combined_rationale = "All translations are acceptable."
        
    except Exception:
        print(f"Error evaluating translation: {traceback.format_exc()}")
        metric = 0
        combined_rationale = "Translation evaluation failed."
    
    return Feedback(
        name="text_translation_score",
        value=metric,
        rationale=combined_rationale,
        metadata={
            "summary_of_translations": summary_of_translations_metadata,
        }
    )


class TextTranslationEvaluator(MLflowEvaluatorBase):
    """Evaluator for text translation accuracy."""

    def __init__(self, global_config: Dict[str, Any], task_config: Dict[str, Any], output_dir: Path):
        super().__init__(global_config, task_config, output_dir)

        self.base_language = Language.from_code(global_config.get("input_language", "en"))
        self.target_language = Language.from_code("es")

    async def process_case(self, step: int, test_case: Dict[str, Any], use_cached_llm_results) -> Dict[str, Any]:
        """Legacy path: TextTypeEvaluator runs via mlflow.genai.evaluate."""
        raise NotImplementedError("TextTypeEvaluator uses mlflow.genai.evaluate.")

    def build_eval_dataset(self, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        for step, tc in enumerate(cases):
            test = tc["data"]
            latest_annotation = max(tc["annotations"], key=lambda x: x["updated_at"])
            truth = [i["result"] for i in tc["annotations"] if i["id"] == latest_annotation["id"]][0]
            page_image_path = self.download_azure_image(
                test["page_image"],
                f"text_extraction_page_{tc['id']}.png",
            )
            
            page_text_list = [
                (
                    t["id"],
                    t["value"]["taxonomy"][0][0] if t["value"].get("taxonomy") else "",
                    t["value"]["text"]
                )
                for t in truth
            ]

            records.append(
                {
                    "inputs": {
                        "case_id": tc["id"],
                        "step": step,
                        "page_text_all": test["page_text_all"],
                        "page_image_path": str(page_image_path),
                        "book_title": test["book_name"],
                        "page_number": test["page_id"],
                        "label_studio_project": tc["project"],
                        "page_text_list": page_text_list,
                        "base_language": self.base_language,
                        "target_language": self.target_language,
                        "scorers": self.task_config.get("scorers", {}),
                    },
                    "expectations": {},
                }
            )
        return records

    def predict_fn(self, **inputs: Any) -> Dict[str, Any]:
        page_text_all = inputs["page_text_all"]
        page_image_path = inputs["page_image_path"]
        page_text_list = inputs["page_text_list"]
        
        page_text_translations = []

        use_cached_llm_results = self.global_config["eval"]["use_cached_llm_results"]
        cache_path = f"{self.output_dir}/logs/text_translation/text_translation_eval_{inputs['case_id']}.json"
        if use_cached_llm_results and os.path.exists(cache_path):
            print(f"Skipping LLM call for case {inputs['case_id']} and using cached results from the logs.")
            page_text_translations = load_json(cache_path)
        else:
            output_page_text_translations = self._run_coro(
                get_text_translation(
                    self.prompt_config,
                    page_text_list,
                    self.base_language,
                    self.target_language,
                )
            )

            page_text_translations = [
                page_text_translation.model_dump()
                for page_text_translation in output_page_text_translations
            ]
            
            #save to cache
            save_json(cache_path, page_text_translations)

        # build eval_page_text_translations
        eval_page_text_translations = build_eval_translations(
            page_text_list,
            page_text_translations,
        )

        return {
            "case_id": inputs["case_id"],
            "step": inputs["step"],
            "book_title": inputs["book_title"],
            "page_number": inputs["page_number"],
            "label_studio_url": (
                f"https://{self.label_studio_config.host}/projects/{inputs['label_studio_project']}/data?task={inputs['case_id']}"
            ),
            "page_text_all": page_text_all,
            "page_image_path": str(Path(page_image_path).relative_to(self.output_dir)),
            "eval_page_text_translations": eval_page_text_translations
        }

    def get_scorers(self) -> List[Any]:
        return [is_acceptable_translation]

    def get_report_results_and_metrics(self, eval_results):
        result_df = eval_results.result_df.copy()
        results = []
        combined_is_translation_acceptable_results =[]
        for index, row in result_df.iterrows():
            output = row.get("response", {})
            assessments = row.get("assessments", {})

            page_text_scorer_scores_list = ast.literal_eval(assessments[0]['metadata']['summary_of_translations'])
            eval_page_text_translations = output["eval_page_text_translations"]

            eval_page_text_translations_with_scores = build_eval_translations_with_scores(
                page_text_scorer_scores_list, 
                eval_page_text_translations
            )

            combined_is_translation_acceptable_results = combined_is_translation_acceptable_results + [t['is_translation_acceptable'] for t in page_text_scorer_scores_list]

            results.append({
                "id": output.get("case_id"),
                'step': index + 1,
                'page_number': output['page_number'],
                'book_title': output['book_title'],
                'page_text': output['page_text_all'],
                'page_image_path': output['page_image_path'],
                'score': assessments[0].get("feedback")['value'],
                'translations': eval_page_text_translations_with_scores,
            })

        #get the metrics
        metrics ={}
        metrics["score"] = round(sum(combined_is_translation_acceptable_results)/len(combined_is_translation_acceptable_results), 2)
        return results, metrics
