"""Text extraction evaluation implementation."""

import os
import fsspec
import mlflow
from pathlib import Path
from typing import Dict, List, Any
from label_studio_sdk.client import LabelStudio

from adt_eval.base import BaseEvaluator
from adt_eval.types import LabelStudioConfig, EvaluationConfig, AzureStorageConfig
from adt_press.llm.text_extraction import get_page_text
from adt_press.models.config import PromptConfig, TemplateConfig
from adt_press.models.pdf import Page
from adt_press.utils.html import render_template


class TextExtractionEvaluator(BaseEvaluator):
    """Evaluator for text extraction accuracy."""
    
    def __init__(self, global_config: Dict[str, Any], task_config: Dict[str, Any], output_dir: Path):
        super().__init__(global_config, task_config, output_dir)
        
        # Extract configurations
        self.label_studio_config = LabelStudioConfig(**global_config["eval"]["label_studio"])
        self.azure_storage_config = AzureStorageConfig(**global_config["eval"]["azure_storage"])
        
        # Setup prompt configuration
        self.prompt_config = PromptConfig.model_validate(task_config["prompt"])
        self.prompt_config.model = task_config["model"]
    
    def load_data(self) -> List[Dict[str, Any]]:
        """Load test cases from Label Studio."""
        label_studio_url = f"https://{self.label_studio_config.url}"
        ls_client = LabelStudio(
            base_url=label_studio_url, 
            api_key=self.label_studio_config.api_key
        )
        
        response = ls_client.projects.list()
        project_ids = {i.title: i.id for i in response.items}
        
        project_id = project_ids[self.task_config["label_studio_project_name"]]
        data = ls_client.projects.exports.as_json(project_id)
        
        return data
    
    async def process_case(self, step: int, tc: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single test case."""
        # Skip cases without annotations
        if not tc["annotations"]:
            return None
        
        test = tc["data"]
        text = test["page_text_all"]
        page_image_url = test["page_image"]
        page_image_url = page_image_url.replace("azure-blob", "az")
        
        truth = tc["annotations"][0]["result"]
        
        # Download image
        local_image_path = self.image_dir / f"page_{tc['id']}.png"
        with fsspec.open(
            page_image_url, 
            account_name=self.azure_storage_config.account_name, 
            account_key=self.azure_storage_config.account_key
        ) as f:
            with open(local_image_path, "wb") as out:
                out.write(f.read())
        
        result = {
            "id": tc["id"],
            "page_text": text,
            "page_image_path": f"./images/page_{tc['id']}.png",
        }
        
        # Create page object for processing
        page = Page(
            page_id=f"p{test['page_id']}",
            page_number=test["page_id"],
            text=text,
            page_image_path=str(local_image_path),
            images=[]
        )
        
        print(f"[{tc['id']:8d}] {text[:65].replace('\n', ' '):<70s}")
        
        # Get page text analysis
        page_texts = await get_page_text(self.prompt_config, page)
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
            
            matches.append({
                "text": text_content,
                "expected": text_type,
                "actual": actual_type,
            })
            
            # Remove from actual results
            if text_content in actual_type_by_text:
                del actual_type_by_text[text_content]
        
        # Add unmatched actual results
        for text_content, actual_type in actual_type_by_text.items():
            matches.append({
                "text": text_content,
                "expected": None,
                "actual": actual_type,
            })
        
        # Log to MLflow
        mlflow.log_dict(page.model_dump(), f"inputs/{step}.json")
        
        for match in matches:
            mlflow.log_table(match, f"results/{step}.json")
        
        # Calculate score
        correct_matches = sum(1 for m in matches if m["expected"] == m["actual"])
        page_score = correct_matches / len(matches) if matches else 1.0
        
        result.update({
            "page_score": page_score,
            "step": step,
            "matches": matches,
        })
        
        mlflow.log_metric("page_score", page_score, step=step)
        
        return result
    
    def generate_report(self, results: List[Dict[str, Any]], metrics: Dict[str, Any]):
        """Generate HTML report."""
        render_template(
            TemplateConfig(output_dir=str(self.output_dir)),
            "templates/eval/text_extraction_report.html",
            {
                "prompt": self.prompt_config,
                "results": results,
                "overall_score": metrics["overall_score"],
            },
        )
