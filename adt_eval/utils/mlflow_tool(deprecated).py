from __future__ import annotations
import pandas as pd
import mlflow
from adt_press.utils.file import cached_read_text_file
from adt_press.models.config import PromptConfig
from typing import Dict, Any
from pathlib import Path
from mlflow.tracking import MlflowClient

from pathlib import Path
from typing import Any, Dict, Mapping, Iterable
from mlflow.genai.datasets import create_dataset, search_datasets
import ast

import logging

def _parse_dict_column(x):
    if isinstance(x, str) and x.strip():
        return ast.literal_eval(x)
    return {}   # fallback if empty/NaN

def _normalize_tags(raw_tags: Any) -> Dict[str, Any] | None:
    """
    Convert task_config-style tags to the dict[str, Any] that MLflow expects.

    Supported forms:
      - dict: {"k": "v", ...}
      - list of {"key": "...", "value": "..."}
      - list of (key, value) 2-tuples
    """
    if raw_tags is None:
        return None

    # Already a mapping -> convert to plain dict
    if isinstance(raw_tags, Mapping):
        return dict(raw_tags)

    # Otherwise try to treat it as an iterable of tag items
    tags_dict: Dict[str, Any] = {}
    try:
        for item in raw_tags:
            if item is None:
                continue

            # e.g. {"key": "lang_pair", "value": "en-es"}
            if isinstance(item, Mapping):
                key = item.get("key")
                value = item.get("value")
                if key is None:
                    continue
                tags_dict[key] = value
            else:
                # e.g. ("lang_pair", "en-es")
                key, value = item
                tags_dict[str(key)] = value
    except TypeError:
        raise TypeError(
            f"tags must be a dict or iterable of mappings/2-tuples, got {type(raw_tags)}"
        )

    return tags_dict or None

class MLflowTool:
    def __init__(self, global_config: Dict[str, Any], task_config: Dict[str, Any], output_dir: Path):
        self.global_config = global_config
        self.task_config = task_config
        self.output_dir = output_dir

        self.client = MlflowClient()

    def _mlflow_check_if_prompt_exists(self, name: str, version: int = 1):
        prompt = mlflow.genai.load_prompt(
                    name_or_uri=name, 
                    version = version,  # or f"prompts:/{prompt_name}@latest"
                    allow_missing=True,
            )
        return prompt is not None

    def get_dataset_id(self, experiment_id: str, dataset_name: str):
        results = search_datasets(
                    experiment_ids=[experiment_id],
                    filter_string=f"name = '{dataset_name}'",
                )
        if len(results) == 0:
            raise ValueError(f"Dataset '{dataset_name}' not found for experiment '{experiment_id}'.")
        
        return results[0].dataset_id

    def mlflow_load_prompt(self, name: str = None, uri: str = None, version: int = 1):
        if name is not None:
            return mlflow.genai.load_prompt(
                        name_or_uri=name, 
                        version = version,
                        allow_missing=True,
                )
        elif uri is not None:
            return mlflow.genai.load_prompt(
                        name_or_uri=uri, 
                        allow_missing=True,
                )
        else:
            raise ValueError("Either name or uri must be provided")

    def list_prompt_versions(self, prompt_name: str):
        versions = []
        for version in itertools.count(1):
            p = mlflow.genai.load_prompt(
                name_or_uri=prompt_name,
                version=version,
                allow_missing=True
            )
            if p is None:
                break
            versions.append(version)
        return versions

    def register_prompt(
        self,
        prompt_name: str,
        template_path: str,
        commit_message: str = None,
        prompt_version: str = None,
        tags: dict[str, str] = None,
    ):
        """
        Register a prompt in MLflow's prompt registry.

        If `create_new_version` is False and the prompt already exists,
        no new version is created and the function returns None.
        """

        #load template
        template_path = Path(template_path)
        if not template_path.exists():
            raise ValueError(f"Template path '{template_path}' does not exist.")
        
        prompt_template = cached_read_text_file(template_path)

        #check if prompt already exists
        prompt_already_exists = self._mlflow_check_if_prompt_exists(prompt_name, prompt_version)
        
        # Only register if the requested version doesn't exist
        if prompt_already_exists and prompt_version is not None:
            return None

        return mlflow.genai.register_prompt(
            name=prompt_name,
            template=prompt_template,
            commit_message=commit_message,
            tags=tags,
        )

    def create_eval_dataset(self, dataset_name: str, mlflow_experiment_name: str) -> None:
        """Create evaluation dataset from MLflow experiment."""

        dataset = create_dataset(
            name=dataset_name,
            experiment_id=mlflow.get_experiment_by_name(mlflow_experiment_name).experiment_id,
            tags={"stage": "validation", "domain": "customer_support"},
        )

        return dataset

    def get_best_run_by_metric(self, experiment_name: str, metric_name: str):

        # Get experiment ID
        experiment = self.client.get_experiment_by_name(experiment_name)
        if experiment is None:
            raise ValueError(f"Experiment '{experiment_name}' not found.")
        experiment_id = experiment.experiment_id

        #Get experiment runs
        runs_df = mlflow.search_runs(
            experiment_ids=[experiment_id],
            order_by=["start_time DESC"],
        )

        metric_key = f"metrics.{metric_name}/mean" #TODO: handle multiple metrics
        filter = (
            (runs_df['status']=="FINISHED") & 
            (runs_df[metric_key] == runs_df[metric_key].max())
        )

        runs_df = runs_df[filter]
        if len(runs_df) == 0:
            return None

        return runs_df.head().to_dict(orient="records")[0]

    def get_traces(self, run_id: str) -> pd.DataFrame:
        """Retrieve traces for the given run."""
        return mlflow.search_traces(run_id=run_id)

    def get_assessments(self, traces_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract trace assessments into a flattened DataFrame.
        Returns all assessments including feedback=True/False.
        """
        assessments = [
            assessment
            for entry in traces_df["assessments"].dropna()
            for assessment in entry
            if "feedback" in assessment
        ]

        if not assessments:
            return pd.DataFrame()

        df = pd.DataFrame(assessments)
        df["metric_value"] = df["feedback"].apply(lambda x: x["value"])

        df = df.merge(
            traces_df[["trace_id", "request", "response"]],
            on="trace_id",
            how="left"
        )

        return df

    def _get_experiment_id(self, experiment_name: str) -> str:
        """
        Resolve an experiment name to its ID.
        """
        experiment = self.client.get_experiment_by_name(experiment_name)
        if experiment is None:
            raise ValueError(f"Experiment '{experiment_name}' not found.")
        return experiment.experiment_id

    def get_experiment_datasets(self, experiment_id: str) -> list:
        """Get all datasets for a given experiment."""
        datasets = search_datasets(experiment_ids=[experiment_id])
        return [{'id': ds.dataset_id, 'name': ds.name, 'tags': ds.tags} for ds in datasets]

    def _create_new_dataset(
        self,
        name: str,
        experiment_name: str,
        tags: Any,
        source_path: str,
    ) -> None:
        """
        Create a new MLflow evaluation dataset and associate it with an experiment.
        """
        experiment_id = self._get_experiment_id(experiment_name)
        normalized_tags = _normalize_tags(tags)

        #load data from CSV
        #load the dataset data
        import pandas as pd
        df = pd.read_csv(source_path)

        for col in ["inputs", "expectations"]:
            df[col] = df[col].apply(_parse_dict_column)
        
        data = df.to_dict('records')

        dataset = create_dataset(
            name=name,
            experiment_id=experiment_id,
            tags=normalized_tags,
        )
        
        print("Created dataset:", dataset.dataset_id)

        dataset.merge_records(data)

        logging.info(
            "Created dataset '%s' (id=%s) for experiment '%s' (id=%s)",
            dataset.name,
            dataset.dataset_id,
            experiment_name,
            experiment_id,
        )

    def create_datasets_if_not_exist(
        self,
        task_config: Dict[str, Any],
    ) -> None:
        """
        Ensure all datasets declared in task_config exist for the given experiment.

        Expected task_config structure (example):

        task_config = {
            "mlflow_experiment_name": "adt_press_translation_task_experiment_dev",
            "datasets": [
                {
                    "name": "translation_eval_v1",
                    "source_path": "data/translation_eval_v1.csv",
                    "tags": [
                        {"key": "version", "value": "1.0"},
                        {"key": "purpose", "value": "translation_regression"},
                    ],
                },
                ...
            ],
        }
        """

        for experiment in task_config['experiments']:

            experiment_id = self._get_experiment_id(experiment['name'])

            for ds in experiment.get("datasets", []):
                dataset_name = ds["name"]
                source_path = Path(ds["source_path"])
                raw_tags = ds.get("tags")

                # 1) Validate the CSV path exists (but don't load it here)
                if not source_path.exists():
                    raise FileNotFoundError(f"Dataset file not found: {source_path}")

                # 2) Check if the dataset already exists for this experiment
                existing = search_datasets(
                    experiment_ids=[experiment_id],
                    filter_string=f"name = '{dataset_name}'",
                )

                if not existing:
                    self._create_new_dataset(
                        name=dataset_name,
                        experiment_name=experiment['name'],
                        tags=raw_tags,
                        source_path=str(source_path),
                    )
                else:
                    logging.info("Dataset '%s' already exists; skipping creation", dataset_name)

    def create_experiment_if_not_exist(self, experiment_name: str) -> str:
        """Create an experiment if it doesn't already exist."""

        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment:
            logging.info("Experiment '%s' already exists, skipping creation", experiment_name)
            return experiment.experiment_id

        experiment_id = mlflow.create_experiment(experiment_name)
        logging.info("Created new experiment '%s'", experiment_name)
        return experiment_id

    def create_experiments_if_not_exist(self, task_config: Dict[str, Any]) -> None:
        "creates experiments in the task configs"
        for experiment in task_config['experiments']:
            self.create_experiment_if_not_exist(experiment['name'])

    def create_prompts_if_not_exist(self, task_config: Dict[str, Any]) -> None:
        """Create prompts for the given task config if they don't already exist."""

        for experiment in task_config['experiments']:
            for prompts in experiment.get("prompts", []):
                for prompt_version in prompts.get("versions", []):
                    result = self.register_prompt(
                        prompt_name = prompts['name'], 
                        template_path = prompt_version['template_path'], 
                        prompt_version = prompt_version['version']
                    )
                    if result is None:
                        logging.info("Prompt '%s' version %s already exists; skipping creation", prompts['name'], prompt_version['version'])
                    else:
                        if str(result.version) == str(prompt_version['version']):
                            logging.info("Created new prompt '%s' version %s", prompts['name'], prompt_version['version'])
                        else:
                            logging.warning("Created new prompt '%s' version %s, instead of version %s requested as it was not the next available prompt version in MLflow. Please update the 'eval_config.yaml' config file to use the correct version.", prompts['name'], result.version, prompt_version['version'])




        
