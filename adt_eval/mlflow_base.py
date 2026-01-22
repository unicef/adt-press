"""MLflow-backed evaluator base class using mlflow.genai.evaluate."""

from __future__ import annotations

import inspect
from abc import abstractmethod
from datetime import datetime
from typing import Any, Dict, List

import mlflow

from adt_eval.base import BaseEvaluator


class MLflowEvaluatorBase(BaseEvaluator):
    """Base evaluator that wraps the core run in an MLflow run."""

    @abstractmethod
    def build_eval_dataset(self, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build MLflow GenAI evaluation dataset rows."""
        raise NotImplementedError

    @abstractmethod
    def predict_fn(self, **inputs: Any) -> Any:
        """Prediction function passed to mlflow.genai.evaluate."""
        raise NotImplementedError

    @abstractmethod
    def get_scorers(self) -> List[Any]:
        """Return scorers for mlflow.genai.evaluate."""
        raise NotImplementedError

    def get_run_name(self) -> str:
        name = self.__class__.__name__.replace("Evaluator", "").lower()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"{name} - {timestamp}"

    def _get_mlflow_config(self) -> Dict[str, Any]:
        eval_cfg = self.global_config.get("eval", {})
        return eval_cfg.get("mlflow", {}) if isinstance(eval_cfg, dict) else {}

    def configure_mlflow(self) -> None:
        mlflow_cfg = self._get_mlflow_config()
        tracking_uri = mlflow_cfg.get("tracking_uri")
        experiment_name = mlflow_cfg.get("experiment_name")

        mlflow.autolog(disable=True)

        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        if experiment_name:
            mlflow.set_experiment(experiment_name)

    def _get_evaluate_kwargs(self) -> Dict[str, Any]:
        mlflow_cfg = self._get_mlflow_config()
        disable_tracing = mlflow_cfg.get("disable_tracing", True)
        kwargs: Dict[str, Any] = {}
        if not disable_tracing:
            return kwargs

        params = inspect.signature(mlflow.genai.evaluate).parameters
        if "disable_tracing" in params:
            kwargs["disable_tracing"] = True
        if "enable_tracing" in params:
            kwargs["enable_tracing"] = False
        if "log_traces" in params:
            kwargs["log_traces"] = False
        return kwargs

    def log_run_params(self) -> None:
        for key, value in self.global_config.items():
            if isinstance(value, (str, int, float, bool)):
                mlflow.log_param(key, value)

    def log_run_metrics(self, metrics: Dict[str, Any]) -> None:
        score = metrics.get("score")
        if score is not None:
            mlflow.log_metric("score", score)

    def get_report_results_and_metrics(self, eval_results) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Return report-ready results and metrics from mlflow.genai.evaluate output."""
        metrics = {}
        if hasattr(eval_results, "metrics"):
            metrics = {key.replace("/mean", ""): value for key, value in eval_results.metrics.items()}
        if "score" not in metrics and "page_score" in metrics:
            metrics["score"] = metrics["page_score"]

        results = []
        if hasattr(eval_results, "result_df"):
            results = eval_results.result_df.to_dict("records")

        return results, metrics

    async def run(self):
        """Main evaluation workflow with MLflow run tracking."""
        self.configure_mlflow()
        run_name = self.get_run_name()
        nested = mlflow.active_run() is not None

        with mlflow.start_run(run_name=run_name, nested=nested):
            self.log_run_params()
            cases = self.filter_cases(self.load_data())
            eval_dataset = self.build_eval_dataset(cases)
            eval_results = mlflow.genai.evaluate(
                data=eval_dataset,
                predict_fn=self.predict_fn,
                scorers=self.get_scorers(),
                **self._get_evaluate_kwargs(),
            )

            results, metrics = self.get_report_results_and_metrics(eval_results)

            self.log_run_metrics(metrics)
            if results and metrics:
                self.generate_report(results, metrics)
            return results, metrics
