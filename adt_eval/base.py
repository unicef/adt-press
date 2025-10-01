"""Base evaluation classes and interfaces."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any
import mlflow
from datetime import datetime


class BaseEvaluator(ABC):
    """Base class for all evaluation types."""
    
    def __init__(self, global_config: Dict[str, Any], task_config: Dict[str, Any], output_dir: Path):
        self.global_config = global_config
        self.task_config = task_config
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create images subdirectory
        self.image_dir = output_dir / "images"
        self.image_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    async def load_data(self) -> List[Dict[str, Any]]:
        """Load test cases from data source."""
        pass
    
    @abstractmethod
    async def process_case(self, step: int, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single test case."""
        pass
    
    async def process_cases(self, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process all test cases with rate limiting."""
        from adt_press.utils import sync
        
        tasks = []
        limit = self.global_config.get("eval", {}).get("limit", 10)
        rate_limit = self.global_config.get("eval", {}).get("rate_limit", 60)
        
        for i, case in enumerate(cases):
            if i >= limit:
                break
            tasks.append(self.process_case(i, case))
        
        # Use adt_press sync utility for rate limiting
        results = [r for r in await sync.gather_with_limit(tasks, rate_limit) if r]
        return results
    
    def calculate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate evaluation metrics."""
        if not results:
            return {"overall_score": 0.0}
        
        overall_score = sum(r.get("page_score", 0.0) for r in results) / len(results)
        return {"overall_score": overall_score}
    
    @abstractmethod
    def generate_report(self, results: List[Dict[str, Any]], metrics: Dict[str, Any]):
        """Generate HTML report."""
        pass
    
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
            results = await self.process_cases(cases)
            
            # Calculate metrics
            metrics = self.calculate_metrics(results)
            mlflow.log_metric("score", metrics["overall_score"])
            
            # Generate report
            self.generate_report(results, metrics)
            
            return results, metrics
