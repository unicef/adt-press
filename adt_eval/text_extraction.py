"""Text extraction evaluation implementation."""

from pathlib import Path
from typing import Any, Dict

import mlflow

from adt_eval.base import BaseEvaluator
from adt_press.llm.text_extraction import get_page_text
from adt_press.models.pdf import Page


class TextExtractionEvaluator(BaseEvaluator):
    """Evaluator for text extraction accuracy."""

    def __init__(self, global_config: Dict[str, Any], task_config: Dict[str, Any], output_dir: Path):
        super().__init__(global_config, task_config, output_dir)

    async def process_case(self, step: int, tc: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single test case."""
        test = tc["data"]
        text = test["page_text_all"]
        page_image_url = test["page_image"]

        page_image_path = self.download_azure_image(page_image_url, f"text_extraction_page_{tc['id']}.png")

        truth = tc["annotations"][0]["result"]
        result = {
            "id": tc["id"],
            "label_studio_url": f"{self.label_studio_config.url}/projects/{tc['project']}/data?task={tc['id']}",
            "page_text": text,
            "page_image_path": str(page_image_path.relative_to(self.output_dir)),
        }

        # Create page object for processing
        page = Page(page_id=f"p{test['page_id']}", page_number=test["page_id"], text=text, page_image_path=str(page_image_path), images=[])

        print(f"[{tc['id']:8d}] {text[:65].replace('\n', ' '):<70s}")

        # Call the LLM for text extraction
        page_texts = await get_page_text(str(self.output_dir), f"eval_{tc['id']}", self.prompt_config, page)
        result["page_texts"] = page_texts.model_dump()

        # Index actual results by text content
        actual_type_by_text = {}
        for group in page_texts.groups:
            for text_item in group.texts:
                actual_type_by_text[text_item.text] = text_item.text_type.value

        # Compare with truth annotations
        matches = []
        for tt in truth:
            text_content = tt["value"]["text"]
            text_type = tt["value"]["taxonomy"][0][0]

            actual_type = actual_type_by_text.get(text_content)

            matches.append(
                {
                    "text": text_content,
                    "expected": text_type,
                    "actual": actual_type,
                }
            )

            # Remove from actual results
            if text_content in actual_type_by_text:
                del actual_type_by_text[text_content]

        # Add unmatched actual results
        for text_content, actual_type in actual_type_by_text.items():
            matches.append(
                {
                    "text": text_content,
                    "expected": None,
                    "actual": actual_type,
                }
            )

        # Log to MLflow
        mlflow.log_dict(page.model_dump(), f"inputs/{step}.json")

        for match in matches:
            mlflow.log_table(match, f"results/{step}.json")

        # Calculate score
        correct_matches = sum(1 for m in matches if m["expected"] == m["actual"])
        score = correct_matches / len(matches) if matches else 1.0

        result.update(
            {
                "score": score,
                "score_count": len(matches),
                "step": step,
                "matches": matches,
            }
        )

        mlflow.log_metric("page_score", score, step=step)

        return result
