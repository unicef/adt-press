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
from typing import Any, Dict

import mlflow
import pandas as pd

from adt_eval.base import BaseEvaluator
from adt_eval.utils.transcript_cleaner import normalize_transcript, standardize_transcript
from adt_press.llm.text_extraction import get_page_text
from adt_press.models.config import TextGroupType, TextType
from adt_press.models.pdf import Page
from adt_press.models.text import PageTextGroups, Text, TextGroup
from adt_press.utils.languages import Language


class TextTypeEvaluator(BaseEvaluator):
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
        """Build PageTexts object from logged JSON file, as an alternative to LLM call."""
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

    async def process_case(self, step: int, tc: Dict[str, Any], use_cached_llm_results: bool) -> Dict[str, Any]:
        """Process a single test case."""

        ## Get the gold standard for test case
        test = tc["data"]
        text = test["page_text_all"]
        page_image_url = test["page_image"]
        book_title = test["book_name"]
        page_number = test["page_id"]

        page_image_path = self.download_azure_image(page_image_url, f"text_extraction_page_{tc['id']}.png")

        # Get the most recent annotation
        latest_annotation = max(tc["annotations"], key=lambda x: x["updated_at"])
        truth = [i["result"] for i in tc["annotations"] if i["id"] == latest_annotation["id"]][0]

        result = {
            "id": tc["id"],
            "book_title": book_title,
            "page_number": page_number,
            "label_studio_url": f"https://{self.label_studio_config.host}/projects/{tc['project']}/data?task={tc['id']}",
            "page_text": text,
            "page_image_path": str(page_image_path.relative_to(self.output_dir)),
        }

        ## Get the LLM candidate output for test case
        # Create page object for processing
        page = Page(page_id=f"p{test['page_id']}", page_number=test["page_id"], text=text, page_image_path=str(page_image_path), images=[])

        print(f"[{tc['id']:8d}] {text[:65].replace('\n', ' '):<70s}")

        # Get input language from config
        input_language_code = self.global_config.get("input_language", "en")
        language = Language.from_code(input_language_code)

        # Call the LLM for text type classification
        if use_cached_llm_results and os.path.exists(f"{self.output_dir}/logs/text_extraction/text_extraction_eval_{tc['id']}.json"):
            print(f"Skipping LLM call for case {tc['id']} and using cached results from the logs.")
            page_texts = self.build_page_texts_from_log(
                Path(f"{self.output_dir}/logs/text_extraction/text_extraction_eval_{tc['id']}.json")
            )
        else:
            page_texts = await get_page_text(
                str(self.output_dir),
                f"eval_{tc['id']}",
                self.prompt_config,
                self.text_types_config,
                self.text_group_types_config,
                page,
                language,
            )

        result["page_texts"] = page_texts.model_dump()

        ## Index LLM candidate results by text content
        actual_type_by_text = {}
        for group in page_texts.groups:
            for text_item in group.texts:
                # Normalize the LLM output for matching
                normalized_key = normalize_transcript(standardize_transcript(text_item.text))

                if normalized_key not in actual_type_by_text.keys():
                    # If text does not yet appear in dictionary, insert as a 1-item list
                    actual_type_by_text[normalized_key] = [text_item.text_type]
                else:
                    # If it exists, add to list
                    actual_type_by_text[normalized_key].append(text_item.text_type)

        ## Compare with gold standard annotations
        matches = []
        for tt in truth:
            if tt["from_name"] == "notes":
                continue

            text_content = tt["value"]["text"]
            taxonomy = tt["value"].get("taxonomy")
            if not taxonomy:
                continue

            text_type = taxonomy[0][0]

            # Some mild cleaning on the text content to match the Gold Standard
            text_content = text_content.replace("\\/", "/")
            text_content = text_content.replace("\\n", "\n")
            text_content = text_content.replace("  ", " ")
            text_content = text_content.replace("\xad", "")

            normalized_content = normalize_transcript(standardize_transcript(text_content))

            # Implement match between ground truth TT and actual LLM result, greedily taking the first text type in the list
            if normalized_content in actual_type_by_text:
                actual_type = actual_type_by_text[normalized_content].pop(0)

                # Remove key if list is empty
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

        # Log to MLflow
        mlflow.log_dict(page.model_dump(), f"inputs/{step}.json")

        mlflow.log_table(pd.DataFrame(matches), f"results/{step}.json")

        # Calculate score
        correct_matches = sum(1 for m in matches if m["expected"] == m["actual"])
        score = correct_matches / len(matches) if matches else 1.0

        result.update(
            {
                "score": score,  # Fraction of correct text type matches
                "score_count": len(matches),  # Number of text type matches attempted
                "step": step,  # Test case number
                "matches": matches,  # List of text type match attempts
            }
        )

        mlflow.log_metric("page_score", score, step=step)

        return result
