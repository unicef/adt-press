"""MLflow-backed evaluator base class using mlflow.genai.evaluate."""

from __future__ import annotations

import asyncio
import inspect
import threading
from abc import abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import mlflow

from adt_eval.base import BaseEvaluator

class AsyncLoopRunner:
    """Run coroutines on a long-lived event loop in a background thread."""

    def __init__(self) -> None:
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._ready = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _runner() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            self._ready.set()
            try:
                loop.run_forever()
            finally:
                try:
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                finally:
                    loop.close()

        self._thread = threading.Thread(target=_runner, daemon=True)
        self._thread.start()
        self._ready.wait()

    def submit(self, coro):
        if not self._loop:
            raise RuntimeError("AsyncLoopRunner not started")
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def close(self) -> None:
        if not self._loop or not self._thread:
            return
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join()
        self._loop = None
        self._thread = None


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

    def _get_experiment_name(self) -> Optional[str]:
        task_cfg = self.task_config.get("experiments_config", {})
        task_experiment = task_cfg.get("experiment_name") if isinstance(task_cfg, dict) else None
        if task_experiment:
            return task_experiment
        return self._get_mlflow_config().get("experiment_name")

    def configure_mlflow(self) -> None:
        mlflow_cfg = self._get_mlflow_config()
        tracking_uri = mlflow_cfg.get("tracking_uri")
        experiment_name = self._get_experiment_name()

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

    def _run_coro(self, coro):
        if not hasattr(self, "_loop_runner") or self._loop_runner is None:
            raise RuntimeError("Async loop runner not initialized")
        return self._loop_runner.submit(coro)

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
        self._loop_runner = AsyncLoopRunner()
        self._loop_runner.start()
        try:
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

        finally:
            self._loop_runner.close()
            self._loop_runner = None
