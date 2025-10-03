"""Base evaluation classes and interfaces."""

import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import fsspec
import mlflow
from label_studio_sdk import LabelStudio

from adt_eval.types import AzureStorageConfig, LabelStudioConfig
from adt_press.models.config import PromptConfig, TemplateConfig
from adt_press.utils.html import render_template


class BaseEvaluator(ABC):
    """Base class for all evaluation types."""

    def __init__(self, global_config: Dict[str, Any], task_config: Dict[str, Any], output_dir: Path):
        self.global_config = global_config
        self.task_config = task_config
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # populate our keys from the environment
        self.label_studio_config = LabelStudioConfig(
            os.environ.get("LABEL_STUDIO_URL", "MISSING_LABEL_STUDIO_URL"),
            os.environ.get("LABEL_STUDIO_KEY", "MISSING_LABEL_STUDIO_KEY"),
        )

        self.azure_storage_config = AzureStorageConfig(
            os.environ.get("AZURE_STORAGE_ACCOUNT_NAME", "MISSING_AZURE_STORAGE_ACCOUNT_NAME"),
            os.environ.get("AZURE_STORAGE_ACCOUNT_KEY", "MISSING_AZURE_STORAGE_ACCOUNT_KEY"),
        )

        # Create images subdirectory
        self.image_dir = output_dir / "images"
        self.image_dir.mkdir(parents=True, exist_ok=True)

        # Setup prompt configuration
        self.prompt_config = PromptConfig.model_validate(task_config["prompt"])
        self.prompt_config.model = task_config["model"]

    def load_data(self) -> List[Dict[str, Any]]:
        """Load test cases from Label Studio."""
        ls_client = LabelStudio(base_url=self.label_studio_config.url, api_key=self.label_studio_config.api_key)

        response = ls_client.projects.list()
        project_ids = {i.title: i.id for i in response.items}

        project_id = project_ids[self.task_config["label_studio_project_name"]]
        data = ls_client.projects.exports.as_json(project_id)

        # sort cases by id so we are deterministic
        data.sort(key=lambda x: x["id"])

        return data

    def filter_cases(self, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter cases, by default we leave out any cases that have no annotations."""
        return [case for case in cases if case.get("annotations")]

    @abstractmethod
    async def process_case(self, step: int, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single test case."""
        pass

    async def process_cases(self, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process all test cases with rate limiting."""
        from adt_press.utils import sync

        tasks = []
        limit = self.global_config["eval"]["limit"]
        rate_limit = self.global_config["eval"]["rate_limit"]

        for i, case in enumerate(cases):
            if i >= limit:
                break
            tasks.append(self.process_case(i, case))

        # Use adt_press sync utility for rate limiting
        results = [r for r in await sync.gather_with_limit(tasks, rate_limit) if r]
        return results

    def generate_report(self, results: List[Dict[str, Any]], metrics: Dict[str, Any]):
        """Generate HTML report."""
        render_template(
            TemplateConfig(output_dir=str(self.output_dir)),
            self.task_config.get("report_template_path"),
            {
                "prompt": self.prompt_config,
                "results": results,
                "score": metrics["score"],
            },
        )

    def download_azure_image(self, image_url: str, filename: str) -> Path:
        image_url = image_url.replace("azure-blob", "az")

        # Download image
        local_image_path = Path(self.image_dir) / filename
        with fsspec.open(
            image_url, account_name=self.azure_storage_config.account_name, account_key=self.azure_storage_config.account_key
        ) as f:
            with open(local_image_path, "wb") as out:
                out.write(f.read())

        return local_image_path

    def calculate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate evaluation metrics."""
        if not results:
            return {"score": 0.0}

        total_score = 0.0
        total_count = 0
        for r in results:
            count = r.get("score_count", 0)
            total_score += r.get("score", 0.0) * count
            total_count += count

        return {"score": total_score / total_count}

    async def run(self):
        """Main evaluation workflow."""
        run_name = f"{self.__class__.__name__.replace('Evaluator', '').lower()} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        with mlflow.start_run(run_name=run_name, nested=True):
            # Log configuration parameters
            for k, v in self.global_config.items():
                if isinstance(v, (str, int, float, bool)):
                    mlflow.log_param(k, v)

            # Load and process data
            cases = self.load_data()

            # filter cases
            cases = self.filter_cases(cases)

            # process all our cases
            results = await self.process_cases(cases)

            # Calculate metrics
            metrics = self.calculate_metrics(results)
            mlflow.log_metric("score", metrics["score"])

            # Generate report
            self.generate_report(results, metrics)

            return results, metrics
