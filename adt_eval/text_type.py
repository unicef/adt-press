"""Text type evaluation implementation.

Some notes on the scoring of matches:
- The LabelStudio text_type dataset sometimes had errors in the text_transcript that were later corrected. Thus, in this script, we correct some of these errors as well (for example, removing double spaces).
- Mismatches are often introduced by mismatched directional quotations, e.g. ’,”,‘,“. These are replaced by non-directional quotations in both the LLM output and the Gold Standard.
- The match strategy implemented is a greedy one.
    - For each line in the LLM output, a list of labels is created (where each item in the list is the text type corresponding to one repetition of the line in the LLM output).
    - For each line in the Gold Standard transcript, we seek a match and, if the line matches, one text type item is 'used up' from the list.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from mlflow.entities import Feedback
from mlflow.genai import scorer

from adt_eval.mlflow_base import MLflowEvaluatorBase
from adt_eval.utils.transcript_cleaner import normalize_transcript, standardize_transcript
from adt_press.llm.text_extraction import get_page_text
from adt_press.models.config import TextGroupType, TextType
from adt_press.models.pdf import Page
from adt_press.models.text import PageTextGroups, Text, TextGroup
from adt_press.utils.languages import Language


@scorer
def text_type_per_page_scorer(inputs: Dict[str, Any], outputs: Dict[str, Any]) -> Feedback:
    truth = inputs.get("truth", [])
    page_texts_data = outputs.get("page_texts") or {}
    page_text_groups = PageTextGroups.model_validate(page_texts_data)

    # Logic to match LLM output to Gold Standard
    matches: List[Dict[str, Any]] = []
    actual_type_by_text: Dict[str, List[str]] = {}
    for group in page_text_groups.groups:
        for text_item in group.texts:
            normalized_key = normalize_transcript(standardize_transcript(text_item.text))
            actual_type_by_text.setdefault(normalized_key, []).append(text_item.text_type)

    for tt in truth:
        if tt["from_name"] == "notes":
            continue

        text_content = tt["value"]["text"]
        taxonomy = tt["value"].get("taxonomy")
        if not taxonomy:
            continue

        text_type = taxonomy[0][0]

        text_content = text_content.replace("\\/", "/")
        text_content = text_content.replace("\\n", "\n")
        text_content = text_content.replace("  ", " ")
        text_content = text_content.replace("\xad", "")

        normalized_content = normalize_transcript(standardize_transcript(text_content))

        if normalized_content in actual_type_by_text:
            actual_type = actual_type_by_text[normalized_content].pop(0)
            if len(actual_type_by_text[normalized_content]) == 0:
                del actual_type_by_text[normalized_content]
        else:
            actual_type = None

        matches.append(
            {
                "text": text_content,
                "expected": text_type,
                "actual": actual_type,
            }
        )

    # Calculate score
    correct_matches = sum(1 for m in matches if m["expected"] == m["actual"])
    score = correct_matches / len(matches) if matches else 1.0

    return Feedback(
        name="text_type_score",
        value=score,
        rationale=json.dumps(matches),
    )


class TextTypeEvaluator(MLflowEvaluatorBase):
    """Evaluator for text type accuracy."""

    def __init__(self, global_config: Dict[str, Any], task_config: Dict[str, Any], output_dir: Path):
        super().__init__(global_config, task_config, output_dir)

        # Build text_types_config from global config
        self.text_types_config = {}
        for name, text_type in global_config.get("text_types", {}).items():
            params = dict(text_type)
            params["name"] = name
            self.text_types_config[name] = TextType.model_validate(params)

        # Build text_group_types_config from global config
        self.text_group_types_config = {}
        for name, text_group_type in global_config.get("text_group_types", {}).items():
            params = dict(text_group_type)
            params["name"] = name
            self.text_group_types_config[name] = TextGroupType.model_validate(params)

    def build_page_texts_from_log(self, fpath: Path) -> PageTextGroups:
        """Build PageTextGroups object from logged JSON file, as an alternative to LLM call."""
        with open(fpath, "r", encoding="utf8") as f:
            page_texts = json.load(f)
            output = page_texts["output"]

        page_text_groups = []
        for g in output["groups"]:
            page_texts = []
            for t in g["texts"]:
                page_text = Text(text_id=t["text_id"], text=t["text"], text_type=t["text_type"])
                page_texts.append(page_text)
            page_text_group = TextGroup(group_id=g["group_id"], group_type=g["group_type"], texts=page_texts)
            page_text_groups.append(page_text_group)
        page_texts = PageTextGroups(page_id=output["page_id"], groups=page_text_groups, reasoning=output["reasoning"])

        return page_texts

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

            records.append(
                {
                    "inputs": {
                        "case_id": tc["id"],
                        "step": step,
                        "page_text": test["page_text_all"],
                        "page_image_path": str(page_image_path),
                        "book_title": test["book_name"],
                        "page_number": test["page_id"],
                        "label_studio_project": tc["project"],
                        "truth": truth,
                    },
                    "expectations": {},
                }
            )
        return records

    def predict_fn(self, **inputs: Any) -> Dict[str, Any]:
        page_text = inputs["page_text"]
        page_image_path = inputs["page_image_path"]

        page = Page(
            page_id=f"p{inputs['page_number']}",
            page_number=inputs["page_number"],
            text=page_text,
            page_image_path=str(page_image_path),
            images=[],
        )

        input_language_code = self.global_config.get("input_language", "en")
        language = Language.from_code(input_language_code)

        use_cached_llm_results = self.global_config["eval"]["use_cached_llm_results"]
        cache_path = f"{self.output_dir}/logs/text_extraction/text_extraction_eval_{inputs['case_id']}.json"
        if use_cached_llm_results and os.path.exists(cache_path):
            page_texts = self.build_page_texts_from_log(Path(cache_path))
            print(f"Skipping LLM call for case {inputs['case_id']} and using cached results from the logs.")
        else:
            page_texts = self._run_coro(
                get_page_text(
                    str(self.output_dir),
                    f"eval_{inputs['case_id']}",
                    self.prompt_config,
                    self.text_types_config,
                    self.text_group_types_config,
                    page,
                    language,
                )
            )

        return {
            "case_id": inputs["case_id"],
            "step": inputs["step"],
            "book_title": inputs["book_title"],
            "page_number": inputs["page_number"],
            "label_studio_url": (
                f"https://{self.label_studio_config.host}/projects/{inputs['label_studio_project']}/data?task={inputs['case_id']}"
            ),
            "page_text": page_text,
            "page_image_path": str(Path(page_image_path).relative_to(self.output_dir)),
            "page_texts": page_texts.model_dump(),
        }

    def get_scorers(self) -> List[Any]:
        return [text_type_per_page_scorer]

    def get_report_results_and_metrics(self, eval_results):
        result_df = eval_results.result_df.copy()
        results: List[Dict[str, Any]] = []
        for _, row in result_df.iterrows():
            # inputs = row.get("request", {})
            outputs = row.get("response", {})
            assessments = row.get("assessments", {})
            rationale = assessments[0].get("rationale", {})
            matches = json.loads(rationale) if rationale else []
            score = row.get("text_type_score/value") or 0

            results.append(
                {
                    "id": outputs.get("case_id"),
                    "book_title": outputs.get("book_title"),
                    "page_number": outputs.get("page_number"),
                    "label_studio_url": outputs.get("label_studio_url"),
                    "page_text": outputs.get("page_text"),
                    "page_image_path": outputs.get("page_image_path"),
                    "page_texts": outputs.get("page_texts"),
                    "score": score,
                    "score_count": len(matches),
                    "step": outputs.get("step"),
                    "matches": matches,
                }
            )

        metrics = {key.replace("/mean", ""): value for key, value in eval_results.metrics.items()}
        metrics["score"] = metrics.get("text_type_score", 0.0)
        return results, metrics
