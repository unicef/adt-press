from __future__ import annotations
import pandas as pd
import mlflow
import tempfile
import os
from .file import cached_read_text_file
from typing import Dict, Any, List
import importlib
from pathlib import Path
from mlflow.tracking import MlflowClient

from pathlib import Path
from typing import Any, Dict, Mapping, Iterable
from mlflow.genai.datasets import create_dataset, search_datasets
import ast
import tempfile

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

def _transform_df(
    df: pd.DataFrame,
    inputs_prefix: str = "inputs.",
    expectations_prefix: str = "expectations.",
) -> List[Dict[str, Any]]:
    """
    Transform a wide DataFrame with prefixed columns into a list of
    nested dictionaries of the form:

        {
            "inputs": {...},
            "expectations": {...},
        }

    Examples
    --------
    Input columns:
        inputs.question, expectations.expected_response
    Output item:
        {
            "inputs": {"question": "..."},
            "expectations": {"expected_response": "..."},
        }

    Parameters
    ----------
    df : pd.DataFrame
        Source DataFrame.
    inputs_prefix : str, optional
        Prefix used for input columns, by default "inputs.".
    expectations_prefix : str, optional
        Prefix used for expectation columns, by default "expectations.".

    Returns
    -------
    List[Dict[str, Any]]
        List of transformed records.
    """
    records: List[Dict[str, Any]] = []

    # Precompute which columns map to inputs/expectations
    input_cols = [c for c in df.columns if c.startswith(inputs_prefix)]
    expectation_cols = [c for c in df.columns if c.startswith(expectations_prefix)]
    
    if not input_cols and not expectation_cols:
        raise ValueError(
            "DataFrame does not contain any columns starting with "
            f"'{inputs_prefix}' or '{expectations_prefix}'."
        )

    for row in df.to_dict(orient="records"):
        inputs: Dict[str, Any] = {}
        expectations: Dict[str, Any] = {}

        for col in input_cols:
            key = col[len(inputs_prefix) :]
            inputs[key] = row.get(col)

        for col in expectation_cols:
            key = col[len(expectations_prefix) :]
            expectations[key] = row.get(col)

        records.append(
            {
                "inputs": inputs,
                "expectations": expectations,
            }
        )

    return records

def _load_prompt_from_module(module_path: str, variable_name: str) -> str:
    """
    Load a prompt string from a Python file path, e.g. 'src/astra/utils/prompts.py'.
    """
    path = Path(module_path)

    if not path.exists():
        raise FileNotFoundError(f"Module file not found: {module_path}")

    module_name = path.stem  # arbitrary name for this module
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    try:
        prompt_content = getattr(module, variable_name)
    except AttributeError:
        raise AttributeError(
            f"Variable '{variable_name}' not found in module '{module_name}' "
            f"loaded from '{module_path}'."
        )

    return prompt_content

class MLflowTool:
    def __init__(self, global_config: Dict[str, Any], task_config: Dict[str, Any], output_dir: Path):
        self.global_config = global_config
        self.task_config = task_config
        self.output_dir = output_dir

        self.client = MlflowClient()

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

    def _mlflow_check_if_prompt_version_exists(self, name: str, version: int = 1):
        prompt = mlflow.genai.load_prompt(
                    name_or_uri=name, 
                    version = version,  # or f"prompts:/{prompt_name}@latest"
                    allow_missing=True,
            )
        return prompt, prompt is not None

    def _create_new_dataset(
        self,
        name: str,
        experiment_name: str,
        experiment_id: str,
        tags: Any,
        data: List[Dict[str, Any]],
    ) -> str:
        """
        Create a new MLflow evaluation dataset and associate it with an experiment.
        """
        normalized_tags = _normalize_tags(tags)

        dataset = create_dataset(
            name=name,
            experiment_id=experiment_id,
            tags=normalized_tags,
        )
        
        dataset.merge_records(data)

        logging.info(
            "Created dataset '%s' (id=%s) for experiment '%s' (id=%s)",
            dataset.name,
            dataset.dataset_id,
            experiment_name,
            experiment_id,
        )
        return dataset

    def create_dataset_if_not_exist(
        self,
        dataset_name: str,
        experiment_name: str,
        data: List[Dict[str, Any]],
        tags: dict[str, str],
    ):
        raw_tags = tags

        # 1) Check if the dataset already exists for this experiment
        experiment_id = self.get_experiment_id(experiment_name)
        existing_ds_list = search_datasets(
            experiment_ids=[experiment_id],
            filter_string=f"name = '{dataset_name}'",
        )

        if len(existing_ds_list) == 0:
            ds =self._create_new_dataset(
                name=dataset_name,
                experiment_name=experiment_name,
                experiment_id=experiment_id,
                tags=raw_tags,
                data=data,
            )
        else:
            logging.info("Dataset '%s' already exists; skipping creation", dataset_name)
            ds = existing_ds_list[0]

        return ds.dataset_id

    def register_prompt_from_module(
        self,
        prompt_name: str,
        prompt_version: int,
        prompts_module_path: str,
        prompt_variable_name: str,
        commit_message: str = None,
        tags: dict[str, str] = None,
    )-> str:
        """
        Register a prompt in MLflow's prompt registry.

        If `create_new_version` is False and the prompt already exists,
        no new version is created and the function returns None.
        """

        #check if prompt already exists
        prompt, prompt_version_already_exists = self._mlflow_check_if_prompt_version_exists(prompt_name, prompt_version)

        # Only register if the requested version doesn't exist
        if prompt_version_already_exists and prompt_version is not None:
            return prompt

        prompt_template = _load_prompt_from_module(
            module_path=prompts_module_path,
            variable_name=prompt_variable_name
        )

        return mlflow.genai.register_prompt(
                    name=prompt_name,
                    template=prompt_template,
                    commit_message=commit_message,
                    tags=tags,
                )

    def register_prompt_from_template(
        self,
        prompt_name: str,
        template_path: str,
        commit_message: str = None,
        prompt_version: str = None,
        tags: dict[str, str] = None,
    )-> str:
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
        prompt, prompt_version_already_exists = self._mlflow_check_if_prompt_version_exists(prompt_name, prompt_version)

        # Only register if the requested version doesn't exist
        if prompt_version_already_exists and prompt_version is not None:
            return prompt

        return mlflow.genai.register_prompt(
            name=prompt_name,
            template=prompt_template,
            commit_message=commit_message,
            tags=tags,
        )

    def create_prompt_if_not_exist(
        self,
        prompt_name: str,
        prompt_version: int,
        tags: dict[str, str] = None,
        template_path: str = None,
        prompts_module_path: str = None,
        prompt_variable_name: str = None,  
    ) -> str:

        prompt, prompt_version_already_exists = self._mlflow_check_if_prompt_version_exists(prompt_name, prompt_version)

        if prompt_version_already_exists:
            logging.info("Prompt '%s' version %s already exists; skipping creation", prompt_name, prompt_version)
            return prompt.uri

        if template_path is not None:
            result = self.register_prompt_from_template(
                prompt_name = prompt_name, 
                template_path = template_path, 
                prompt_version = prompt_version,
                tags = tags
            )
        else:
            result = self.register_prompt_from_module(
                prompt_name = prompt_name, 
                prompts_module_path = prompts_module_path,
                prompt_variable_name = prompt_variable_name,
                prompt_version = prompt_version,
                tags = tags
            )

        if str(result.version) == str(prompt_version):
            logging.info("Created new prompt '%s' version %s", prompt_name, prompt_version)
        else:
            logging.warning("Created new prompt '%s' version %s, instead of version %s requested as it was not the next available prompt version in MLflow. Please update the 'eval_config.yaml' config file to use the correct version.", prompt_name, result.version, prompt_version)

        return result.uri

    def get_experiment_id(self, experiment_name: str) -> str:
        """
        Resolve an experiment name to its ID.
        """
        experiment = self.client.get_experiment_by_name(experiment_name)
        if experiment is None:
            raise ValueError(f"Experiment '{experiment_name}' not found.")
        return experiment.experiment_id

    def get_best_run_by_metric(self, experiment_id: str, metric_name: str):

        #Get experiment runs
        runs_df = mlflow.search_runs(
            experiment_ids=[experiment_id],
            order_by=["start_time DESC"],
        )

        if len(runs_df) == 0:
            return None

        metric_key = f"metrics.{metric_name}/mean" #TODO: handle multiple metrics
        filter = (
            (runs_df['status']=="FINISHED") & 
            (runs_df[metric_key] == runs_df[metric_key].max())
        )

        runs_df = runs_df[filter]
        if len(runs_df) == 0:
            print(f"No runs found for experiment '{experiment_name}' with metric '{metric_name}'.")
            return None

        return runs_df.head().to_dict(orient="records")[0]

    def log_markdown_as_artifact(self, markdown_str: str, artifact_name: str = "report.md"):
        """
        Logs a markdown string as an MLflow artifact.

        Parameters
        ----------
        markdown_str : str
            The markdown content to store.
        artifact_name : str
            The filename to use in the MLflow artifact store.
        """

        # Create a temporary file
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, artifact_name)

            # Write markdown content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown_str)

            # Log to MLflow
            mlflow.log_artifact(file_path)

            print(f"Logged markdown artifact: {artifact_name}")

    def analysis_to_markdown(self, analysis: Dict[str, Any]) -> str:
        """Convert prompt analysis model_dump into a structured Markdown report."""

        lines: List[str] = []

        # ------------------------------------------------------------------ #
        # Header
        # ------------------------------------------------------------------ #
        risk = analysis.get("risk_level", "unknown").upper()
        confidence = analysis.get("confidence")
        summary = analysis.get("summary", "")

        lines.append("# Prompt Analysis Report")
        lines.append("")
        lines.append(f"- **Risk level:** `{risk}`")
        if confidence is not None:
            lines.append(f"- **Model confidence:** `{confidence:.2f}`")
        lines.append("")
        lines.append("## 1. High-level Summary")
        lines.append("")
        if summary:
            lines.append(summary)
        else:
            lines.append("_No summary provided._")
        lines.append("")

        # ------------------------------------------------------------------ #
        # Global behavior patterns
        # ------------------------------------------------------------------ #
        global_patterns = analysis.get("global_behavior_patterns", [])
        lines.append("## 2. Global Behavior Patterns")
        lines.append("")
        if global_patterns:
            for p in global_patterns:
                lines.append(f"- {p}")
        else:
            lines.append("_No global patterns identified._")
        lines.append("")

        # ------------------------------------------------------------------ #
        # Per-case analysis
        # ------------------------------------------------------------------ #
        per_case = analysis.get("per_case_analysis", [])
        lines.append("## 3. Per-case Analysis")
        lines.append("")
        if not per_case:
            lines.append("_No per-case analysis available._")
        else:
            for case in per_case:
                case_no = case.get("case_no", "?")
                short_summary = case.get("short_summary", "").strip()
                outcome_severity = case.get("outcome_severity", "unknown")
                issue_type = case.get("issue_type", "unknown")

                lines.append(f"### Case {case_no}")
                lines.append("")
                if short_summary:
                    lines.append(short_summary)
                    lines.append("")
                lines.append(f"- **Outcome severity:** `{outcome_severity}`")
                lines.append(f"- **Issue type:** `{issue_type}`")

                expected_behavior = case.get("expected_behavior")
                actual_behavior = case.get("actual_behavior")
                metric_signals = case.get("metric_signals", [])
                contributing_root_causes = case.get("contributing_root_causes", [])

                if expected_behavior:
                    lines.append(f"- **Expected behavior:** {expected_behavior}")
                if actual_behavior:
                    lines.append(f"- **Actual behavior:** {actual_behavior}")

                if metric_signals:
                    lines.append("- **Metric signals:**")
                    for m in metric_signals:
                        lines.append(f"  - {m}")

                if contributing_root_causes:
                    ids = ", ".join(str(i) for i in contributing_root_causes)
                    lines.append(f"- **Contributing root cause IDs:** {ids}")

                lines.append("")

        # ------------------------------------------------------------------ #
        # Root causes
        # ------------------------------------------------------------------ #
        root_causes = analysis.get("root_causes", [])
        lines.append("## 4. Root Causes")
        lines.append("")
        if not root_causes:
            lines.append("_No root causes identified._")
        else:
            for rc in root_causes:
                rc_id = rc.get("id", "?")
                area = rc.get("area", "unspecified")
                explanation = rc.get("explanation", "")
                pattern = rc.get("pattern_across_cases", "")
                affected_cases = rc.get("affected_cases", [])

                lines.append(f"### Root Cause {rc_id}: {area}")
                lines.append("")
                if explanation:
                    lines.append(f"**Explanation:** {explanation}")
                if pattern:
                    lines.append(f"**Pattern across cases:** {pattern}")
                if affected_cases:
                    cases_str = ", ".join(str(c) for c in affected_cases)
                    lines.append(f"**Affected cases:** {cases_str}")
                lines.append("")

        # ------------------------------------------------------------------ #
        # Fixes / Recommended Prompt Changes
        # ------------------------------------------------------------------ #
        fixes = analysis.get("fixes", [])
        lines.append("## 5. Recommended Fixes to the Prompt")
        lines.append("")
        if not fixes:
            lines.append("_No fixes proposed._")
        else:
            for fix in fixes:
                fix_id = fix.get("id", "?")
                ftype = fix.get("type", "unspecified")
                target = fix.get("target_section", "unspecified")
                text = fix.get("text", "")
                rationale = fix.get("rationale", "")
                addresses = fix.get("addresses_root_causes", [])

                lines.append(f"### Fix {fix_id}: {ftype} → `{target}`")
                lines.append("")
                if addresses:
                    ids_str = ", ".join(str(i) for i in addresses)
                    lines.append(f"- **Addresses root cause IDs:** {ids_str}")
                if rationale:
                    lines.append(f"- **Rationale:** {rationale}")
                lines.append("")
                if text:
                    lines.append("**Proposed prompt text:**")
                    lines.append("")
                    lines.append("```text")
                    lines.append(text)
                    lines.append("```")
                lines.append("")

        # ------------------------------------------------------------------ #
        # Acceptance criteria
        # ------------------------------------------------------------------ #
        acceptance = analysis.get("acceptance_criteria", [])
        lines.append("## 6. Acceptance Criteria for the Revised Prompt")
        lines.append("")
        if acceptance:
            for crit in acceptance:
                lines.append(f"- {crit}")
        else:
            lines.append("_No acceptance criteria specified._")
        lines.append("")

        # ------------------------------------------------------------------ #
        # Evidence
        # ------------------------------------------------------------------ #
        evidence = analysis.get("evidence", {})
        lines.append("## 7. Evidence and Supporting Quotes")
        lines.append("")

        prompt_quotes = evidence.get("prompt_quotes", [])
        response_quotes = evidence.get("response_quotes", [])
        request_features = evidence.get("request_features", [])
        case_ids = evidence.get("case_ids", [])

        if prompt_quotes:
            lines.append("### 7.1 Prompt Excerpts Driving Behavior")
            lines.append("")
            for q in prompt_quotes:
                lines.append(f"- {q}")
            lines.append("")

        if response_quotes:
            lines.append("### 7.2 Model Response Excerpts")
            lines.append("")
            for q in response_quotes:
                lines.append(f"- {q}")
            lines.append("")

        if request_features:
            lines.append("### 7.3 Request / Input Features")
            lines.append("")
            for f in request_features:
                lines.append(f"- {f}")
            lines.append("")

        if case_ids:
            ids_str = ", ".join(str(i) for i in case_ids)
            lines.append("### 7.4 Cases Considered")
            lines.append("")
            lines.append(f"- **Case IDs analyzed:** {ids_str}")
            lines.append("")
        elif not any([prompt_quotes, response_quotes, request_features]):
            lines.append("_No evidence captured._")
            lines.append("")

        # Join everything
        return "\n".join(lines)


def _messages_to_md(messages) -> str:
    # minimal serializer; customize if you keep LC Message objects in state
    lines = []
    for m in messages or []:
        role = getattr(m, "type", getattr(m, "role", "user"))
        content = getattr(m, "content", str(m))
        lines.append(f"- **{role}**: {content}")
    return "\n".join(lines)