"""Base evaluation classes and interfaces."""

import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import logging

import ast
import pandas as pd
import asyncio
import fsspec
import mlflow
from label_studio_sdk import LabelStudio
from litellm import completion

from adt_eval.types import AzureStorageConfig, LabelStudioConfig
from adt_press.models.config import PromptConfig, TemplateConfig
from adt_press.utils.html import render_template

from adt_eval.schema import PromptAnalystOutput, PromptOptimizerOutput
from adt_eval.utils.mlflow import MLflowTool
from adt_eval.utils.tools import is_running_in_jupyter
from adt_eval.utils.task_config_utils import get_experiment_dataset_name, get_experiment_prompt_name

from adt_eval.utils.image import ImageDownloader



from adt_eval.prompts import (
    PROMPT_ANALYST_SYSTEM_PROMPT,
    PROMPT_OPTIMIZER_SYSTEM_PROMPT,
)

from openai import OpenAI #TODO: use litellm

import logging

logging.getLogger("LiteLLM").setLevel(logging.ERROR)

# Configure logging once at startup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)

mlflow.autolog(disable=True)

class BaseEvaluator(ABC):
    """Base class for all evaluation types."""

    def __init__(self, global_config: Dict[str, Any], task_config: Dict[str, Any], output_dir: Path):
        self.global_config = global_config
        self.task_config = task_config
        self.experiments_cfg = self.task_config.get("experiments") #TODO: support multiple experiments
        self.experiment_run_cfg = self.experiments_cfg[0]

        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create images subdirectory
        self.image_dir = output_dir / "images"
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
        self.dataset_cfg = self.experiment_run_cfg.get("dataset", {})
        self.dataset_cfg['is_label_studio_dataset'] = self.dataset_cfg.get("label_studio_project_name") is not None
        self.prompt_cfg = self.experiment_run_cfg.get("prompt", {})
        self.optimization_cfg = self.prompt_cfg.get("optimization", {})
         
        #set mlflow tracking uri
        self.is_jupyter = is_running_in_jupyter()
        if self.is_jupyter:
            MLFLOW_TRACKING_URI = "http://localhost:5000"
        else:
            MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")

        logging.info(f"Setting the mlflow tracking uri to: {MLFLOW_TRACKING_URI}")
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment(self.experiment_run_cfg["experiment_name"])
        
        #get experiment id
        self.mlflow_tool = MLflowTool(global_config, self.experiment_run_cfg, output_dir)
        self.experiment_run_cfg["experiment_id"] = self.mlflow_tool.get_experiment_id(self.experiment_run_cfg["experiment_name"])

        # populate our keys from the environment
        self.label_studio_config = LabelStudioConfig(
            host=os.environ.get("LABEL_STUDIO_HOST", "MISSING_LABEL_STUDIO_HOST"),
            token=os.environ.get("LABEL_STUDIO_TOKEN", "MISSING_LABEL_STUDIO_TOKEN"),
        )

        self.azure_storage_config = AzureStorageConfig(
            account_name=os.environ.get("AZURE_STORAGE_ACCOUNT_NAME", "MISSING_AZURE_STORAGE_ACCOUNT_NAME"),
            account_key=os.environ.get("AZURE_STORAGE_ACCOUNT_KEY", "MISSING_AZURE_STORAGE_ACCOUNT_KEY"),
        )

        self.image_downloader = ImageDownloader(self.image_dir, self.azure_storage_config)
       
        self.experiment_run_results = None
        self.experiment_run_prompt = {}

        self.eval_dataset_records = None
        self.downloaded_images = None

        self.data = None
        self.user_feedback = None

    def setup_experiment_environment(self):
        """Setup the experiment environment."""

        logging.info("Setting up experiment environment...")
       
        #set the dataset
        self.dataset_cfg["dataset_id"] = self.mlflow_tool.create_dataset_if_not_exist(
            dataset_name=self.dataset_cfg.get("name"),
            experiment_name=self.experiment_run_cfg["experiment_name"],
            data=self.eval_dataset_records,
            tags=self.dataset_cfg.get("tags")
        )

        #set the prompt
        self.prompt_cfg["prompt_uri"] = self.mlflow_tool.create_prompt_if_not_exist(
            prompt_name=self.prompt_cfg.get("name"),
            prompt_version=self.prompt_cfg.get("version"),
            template_path=self.prompt_cfg.get("template_path"),
            prompts_module_path=self.prompt_cfg.get("prompts_module_path"),
            prompt_variable_name=self.prompt_cfg.get("prompt_variable_name"),
        )

    @abstractmethod
    def predict_ftn(self, dialog: str) -> str:
        """Prediction function used by MLflow GenAI evaluation."""
        pass

    @abstractmethod
    def execute_eval_experiment_run(self):
        """Execute the eval experiment run."""
        pass

    @abstractmethod
    def create_eval_dataset_records(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create evaluation dataset records."""
        pass

    @abstractmethod  
    def get_report_results_and_metrics(self):
        """Get report results and metrics."""
        pass

    @abstractmethod  
    def load_prompt_analysis_job_order(self):
        """Load prompt analysis job order."""
        pass

    @abstractmethod
    async def process_case(self, step: int, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single test case."""
        pass

    def _run_coro(self, coro: asyncio.Future) -> Any:
        """
        Run an async coroutine from a sync context, handling Jupyter vs script.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        # Running inside an existing event loop (e.g., Jupyter)
        if self.is_jupyter:
            import nest_asyncio
            nest_asyncio.apply()
        return loop.run_until_complete(coro)
    
    def load_eval_datasets(self) -> None:
        """Load evaluation datasets from task configuration."""
        self.mlflow_tool.add_experiment_datasets(task_config)

    def load_data(self) -> List[Dict[str, Any]]:
        """Load test cases from Label Studio."""

        if self.dataset_cfg['is_label_studio_dataset']:
            return self.load_label_studio_data()
        else:
            return self.load_csv_data()

    def load_label_studio_data(self) -> List[Dict[str, Any]]:
        """Load test cases from Label Studio."""

        ls_client = LabelStudio(base_url=f"https://{self.label_studio_config.host}", api_key=self.label_studio_config.token)

        response = ls_client.projects.list()
        project_ids = {i.title: i.id for i in response.items}

        project_id = project_ids[self.dataset_cfg["label_studio_project_name"]]
        data = ls_client.projects.exports.as_json(project_id)

        # sort cases by id so we are deterministic
        data.sort(key=lambda x: x["id"])

        return data

    def load_csv_data(self) -> List[Dict[str, Any]]:
        """Load test cases from CSV."""

        return pd.read_csv(self.dataset_cfg["source_path"]).to_dict("records")

    def filter_cases(self, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter cases, by default we leave out any cases that have no annotations."""
        return [case for case in cases if case.get("annotations")]

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
            self.experiment_run_cfg.get("report_template_path"),
            {
                "prompt": self.experiment_run_prompt,
                "results": results,
                "score": metrics["score"],
            },
        )

    def download_images(self) -> None:
        """Download images from Azure Blob Storage and update eval records with local paths."""

        def _update_eval_dataset_records(downloaded_images: list[dict]) -> None:
            """Attach local image paths to eval_dataset_records based on downloaded images."""

            # Build fast lookup: url -> local_path
            image_lookup = {
                img["url"]: img["local_path"]
                for img in downloaded_images
                if img.get("url") is not None
            }

            for record in self.eval_dataset_records:
                try:
                    input_text = ast.literal_eval(record["inputs"]["input_text"])
                except (ValueError, SyntaxError) as exc:
                    logging.warning(
                        "Skipping record %s due to invalid input_text: %s",
                        record.get("entry_id"),
                        exc,
                    )
                    continue

                page_image_url = input_text.get("page_image")
                input_text["page_image_local_path"] = str(image_lookup.get(page_image_url))

                # Store back as string (to match original schema)
                record["inputs"]["input_text"] = str(input_text)

        # 1) Build list of images to download
        images: list[dict] = []

        for record in self.eval_dataset_records:
            try:
                input_text = ast.literal_eval(record["inputs"]["input_text"])
            except (ValueError, SyntaxError) as exc:
                logging.warning(
                    "Skipping record %s when building image list due to invalid input_text: %s",
                    record.get("entry_id"),
                    exc,
                )
                continue

            page_image_url = input_text.get("page_image")
            if not page_image_url:
                continue

            images.append(
                {
                    "url": page_image_url,
                    "filename": f"text_extraction_page_{record['entry_id']}.png",
                }
            )

        if not images:
            logging.info("No images found in eval_dataset_records; skipping download.")
            return

        # 2) Download images
        logging.info("Downloading %d images to %s", len(images), self.image_dir)
        downloaded_images = self.image_downloader.download_batch(images)

        # 3) Update eval dataset records with local paths
        _update_eval_dataset_records(downloaded_images)

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

    def run_prompt_analysis(self):
        """Run the prompt analysis."""

        logging.info("Running prompt analysis. This could take several minutes...")

        # Provide the artifact as JSON in the human message
        human_payload = {
            "instruction": "Analyze this analysis_job_order and produce the structured output per schema.",
            "analysis_job_order": self.prompt_analysis_job_order
        }

        response  = completion(
            model="gpt-5",
            messages=[
                {"role": "system", "content": PROMPT_ANALYST_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": str(human_payload),
                },
            ],
            response_format=PromptAnalystOutput,
        )

        msg = response.choices[0].message
        content = msg.content
        self.analysis_output = PromptAnalystOutput.model_validate_json(content)

        return self.analysis_output

    def run_prompt_optimization(self):
        """Run the prompt optimization."""

        analyst_output_payload = self.analysis_output.model_dump()
        human_payload = {
            "instruction": "Revise the prompt_template using analyst_output + user_feedback. Return JSON per schema.",
            "analysis_job_order": self.prompt_analysis_job_order,
            "analyst_output": analyst_output_payload,
            "user_feedback": self.user_feedback,
        }

        logging.info("Running prompt optimizer. This could take several minutes...")
        response = completion(
            model="gpt-5",
            messages=[
                {"role": "system", "content": PROMPT_OPTIMIZER_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": str(human_payload),
                },
            ],
            response_format=PromptOptimizerOutput,
        )

        msg = response.choices[0].message
        content = msg.content
        self.optimizer_output = PromptOptimizerOutput.model_validate_json(content)
        self.optimizer_output.prompt_name = self.prompt_analysis_job_order["prompt_name"]

        logging.info("Completed prompt optimization.")
        return self.optimizer_output

    def register_optimized_prompt(self):
        """Register the optimized prompt."""

        logging.info("Registering optimized prompt...")
        prompt_name = self.optimizer_output.prompt_name
        prompt_template= self.optimizer_output.revised_prompt_template
        optimized_prompt = mlflow.genai.register_prompt(
            name=prompt_name,
            template=prompt_template, 
        )

        logging.info("Registered optimized prompt: %s", optimized_prompt.uri)
        self.optimized_prompt = optimized_prompt
        return self.optimized_prompt

    def run_prompt_optimization_workflow(self):

        logging.info("Running prompt optimization workflow...")
        self.load_prompt_analysis_job_order()
        self.run_prompt_analysis()

        #run prompt optimization
        self.run_prompt_optimization()

        self.register_optimized_prompt()
        self.execute_eval_experiment_run(
            optimized_prompt_uri=self.optimized_prompt.uri
            )

        logging.info("Completed prompt optimization workflow.")

    def run(self):
        """Main evaluation workflow."""

        #load the dataset
        self.data = self.load_data()

        #prepare the dataset
        self.eval_dataset_records = self.create_eval_dataset_records(self.data)

        #filter the dataset
        self.eval_dataset_records = self.eval_dataset_records[:50]

        #download images for the experiment
        self.download_images()
        
        #setup experiment environment
        self.setup_experiment_environment()

        if self.optimization_cfg.get("is_enabled"):
            self.run_prompt_optimization_workflow()
        else:
            self.execute_eval_experiment_run()
      
            #generate report
            results, metrics = self.get_report_results_and_metrics()

            self.results = results
            self.metrics = metrics
            self.generate_report(results, metrics)

        # run_name = f"{self.__class__.__name__.replace('Evaluator', '').lower()} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # with mlflow.start_run(run_name=run_name, nested=True):
        #     # Log configuration parameters
        #     for k, v in self.global_config.items():
        #         if isinstance(v, (str, int, float, bool)):
        #             mlflow.log_param(k, v)

        #     # Load and process data
        #     cases = self.load_data()

        #     # filter cases
        #     cases = self.filter_cases(cases)

        #     # process all our cases
        #     results = await self.process_cases(cases)

        #     # Calculate metrics
        #     metrics = self.calculate_metrics(results)
        #     mlflow.log_metric("score", metrics["score"])

        #     # Generate report
        #     self.generate_report(results, metrics)

        # return results, metrics
