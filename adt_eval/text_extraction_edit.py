"""Text extraction evaluation implementation."""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

import mlflow
import pandas as pd
from dotenv import load_dotenv
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score

from adt_eval.base import BaseEvaluator
from adt_press.llm.text_extraction import get_page_text
from adt_press.models.pdf import Page

# # Setup MLflow tracking
# load_dotenv()
# tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
# if tracking_uri:
#     mlflow.set_tracking_uri(tracking_uri)
#     print(f"MLflow tracking URI: {tracking_uri.split('@')[-1] if '@' in tracking_uri else tracking_uri}")
# # If not set, MLflow will use local filesystem (./mlruns)


class TextExtractionEvaluator(BaseEvaluator):
    """Evaluator for text extraction accuracy across all pages."""

    def __init__(self, global_config: Dict[str, Any], task_config: Dict[str, Any], output_dir: Path):
        super().__init__(global_config, task_config, output_dir)

    async def process_case(self, step: int, tc: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single test case and collect matches."""
        print(f"[{step:3d}] Processing case ID: {tc['id']}")
        
        test = tc["data"]  # tc = test case
        text = test["page_text_all"]
        page_image_url = test["page_image"]

        print(f"[{step:3d}] Downloading page image...")
        page_image_path = self.download_azure_image(page_image_url, f"text_extraction_page_{tc['id']}.png")

        truth = tc["annotations"][0]["result"]
        
        # Extract metadata for tracking
        book_name = test.get("book_name", test.get("file_upload", "unknown"))  # Get book name if available
        if isinstance(book_name, str) and "/" in book_name:
            # Extract filename from path if it's a full path
            book_name = book_name.split("/")[-1].replace(".pdf", "")
        page_number = test.get("page_id", test.get("page_number", "unknown"))
        
        result = {
            "id": tc["id"],
            "label_studio_url": f"https://{self.label_studio_config.host}/projects/{tc['project']}/data?task={tc['id']}",
            "page_text": text,
            "page_image_path": str(page_image_path.relative_to(self.output_dir)),
            "book_name": book_name,
            "page_number": page_number,
        }

        # Create page object for processing
        page = Page(page_id=f"p{test['page_id']}", page_number=test["page_id"], text=text, page_image_path=str(page_image_path), images=[])

        # Call the LLM for text extraction
        print(f"[{step:3d}] Calling LLM for text extraction...")
        page_texts = await get_page_text(str(self.output_dir), f"eval_{tc['id']}", self.prompt_config, page)
        print(f"[{step:3d}] LLM returned {len(page_texts.groups)} groups")
        result["page_texts"] = page_texts.model_dump()

        # Index actual results by text content
        actual_type_by_text = {}
        for group in page_texts.groups:
            for text_item in group.texts:
                actual_type_by_text[text_item.text] = text_item.text_type.value

        # Prepare metadata for all matches
        match_metadata = {
            "task_id": tc["id"],
            "book_name": book_name,
            "page_number": page_number,
            "project_id": tc.get("project", "unknown"),
        }

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
                    **match_metadata,  # Add all metadata fields
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
                    **match_metadata,  # Add all metadata fields
                }
            )

        # Store matches for later aggregation
        result["matches"] = matches
        result["step"] = step
        
        # Calculate individual page score for reporting purposes
        correct_matches = sum(1 for m in matches if m["expected"] == m["actual"])
        result["score"] = correct_matches / len(matches) if matches else 1.0
        result["score_count"] = len(matches)

        # Log input to MLflow (individual page data)
        # NOTE: Disabled due to Azure Blob Storage authentication issues
        # mlflow.log_dict(page.model_dump(), f"inputs/{step}.json")

        print(f"[{step:3d}] ✓ Completed (found {len(matches)} matches, score: {result['score']:.2%})")
        return result

    def calculate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate evaluation metrics across all pages."""
        if not results:
            return {"score": 0.0}

        # Aggregate all matches from all pages
        print(f"\nAggregating matches from {len(results)} results...")
        all_matches = []
        for i, r in enumerate(results):
            matches = r.get("matches", [])
            all_matches.extend(matches)
            print(f"  Result {i}: {len(matches)} matches (total so far: {len(all_matches)})")

        if not all_matches:
            return {"score": 0.0}

        print(f"Total aggregated matches: {len(all_matches)}\n")
        
        # Convert all matches to DataFrame
        all_matches_df = pd.DataFrame(all_matches)
        print(f"DataFrame shape: {all_matches_df.shape}")
        print(f"DataFrame columns: {list(all_matches_df.columns)}")
        print(f"Unique books: {all_matches_df['book_name'].unique()}")

        # Prepare data for sklearn metrics
        # Filter out rows where expected or actual is None
        valid_matches_df = all_matches_df[
            all_matches_df["expected"].notna() & all_matches_df["actual"].notna()
        ].copy()
        
        # Also handle cases where we predicted something but there's no ground truth
        y_true = all_matches_df["expected"].fillna("MISSING_LABEL")
        y_pred = all_matches_df["actual"].fillna("NO_PREDICTION")
        
        # Calculate sklearn metrics
        accuracy = accuracy_score(y_true, y_pred)
        
        # Get unique labels for multiclass metrics
        labels = sorted(set(y_true) | set(y_pred))
        # Remove special labels we added
        labels = [l for l in labels if l not in ["MISSING_LABEL", "NO_PREDICTION"]]
        
        # Calculate precision, recall, f1 with macro averaging
        precision_macro = precision_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
        recall_macro = recall_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
        f1_macro = f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
        
        # Calculate weighted metrics (weighted by support)
        precision_weighted = precision_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)
        recall_weighted = recall_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)
        f1_weighted = f1_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)
        
        # Generate classification report
        report = classification_report(y_true, y_pred, labels=labels, zero_division=0, output_dict=True)
        
        # Generate confusion matrix
        conf_matrix = confusion_matrix(y_true, y_pred, labels=labels)
        conf_matrix_df = pd.DataFrame(
            conf_matrix,
            index=[f"True_{label}" for label in labels],
            columns=[f"Pred_{label}" for label in labels],
        )
        
        # Calculate book-level statistics
        book_stats = []
        for book_name, book_df in all_matches_df.groupby("book_name"):
            book_correct = (book_df["expected"] == book_df["actual"]).sum()
            book_total = len(book_df)
            book_score = book_correct / book_total if book_total > 0 else 0.0
            
            book_stats.append({
                "book_name": book_name,
                "total_matches": book_total,
                "correct_matches": book_correct,
                "score": book_score,
            })
        
        book_stats_df = pd.DataFrame(book_stats)
        
        # Prepare comprehensive metrics dictionary
        metrics = {
            "score": accuracy,  # Use accuracy as the main score
            "accuracy": accuracy,
            "precision_macro": precision_macro,
            "recall_macro": recall_macro,
            "f1_macro": f1_macro,
            "precision_weighted": precision_weighted,
            "recall_weighted": recall_weighted,
            "f1_weighted": f1_weighted,
            "total_matches": len(all_matches),
            "valid_matches": len(valid_matches_df),
            # "num_books": len(book_stats),
        }
        
        # Extract prompt name from template path
        prompt_name = Path(self.prompt_config.template_path).stem if hasattr(self.prompt_config, 'template_path') else 'text_extraction'
        
        # Log all results to MLflow
        self._log_to_mlflow(
            prompt_name=prompt_name,
            all_matches_df=all_matches_df,
            book_stats_df=book_stats_df,
            conf_matrix_df=conf_matrix_df,
            classification_report=report,
            metrics=metrics,
        )
        
        # Print results to console
        self._print_metrics_report(
            prompt_name=prompt_name,
            all_matches_df=all_matches_df,
            valid_matches_df=valid_matches_df,
            metrics=metrics,
            labels=labels,
            report=report,
            conf_matrix_df=conf_matrix_df,
            book_stats=book_stats,
        )

        return metrics
    
    def _print_metrics_report(
        self,
        prompt_name: str,
        all_matches_df: pd.DataFrame,
        valid_matches_df: pd.DataFrame,
        metrics: Dict[str, Any],
        labels: List[str],
        report: Dict[str, Any],
        conf_matrix_df: pd.DataFrame,
        book_stats: List[Dict[str, Any]],
    ) -> None:
        """Print evaluation metrics report to console."""
        from datetime import datetime
        from zoneinfo import ZoneInfo
        
        time_now_cest = datetime.now(ZoneInfo("Europe/Paris"))
        
        print("\n" + "="*80)
        print("=== Overall Classification Metrics ===")
        print("="*80)
        print(f"Prompt: {prompt_name}")
        print(f"Timestamp (CEST): {time_now_cest.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total samples:        {len(all_matches_df)}")
        print(f"Valid predictions:    {len(valid_matches_df)}")
        print(f"\nAccuracy:             {metrics['accuracy']:.4f}")
        print(f"\nMacro Metrics:")
        print(f"  Precision:          {metrics['precision_macro']:.4f}")
        print(f"  Recall:             {metrics['recall_macro']:.4f}")
        print(f"  F1-Score:           {metrics['f1_macro']:.4f}")
        print(f"\nWeighted Metrics:")
        print(f"  Precision:          {metrics['precision_weighted']:.4f}")
        print(f"  Recall:             {metrics['recall_weighted']:.4f}")
        print(f"  F1-Score:           {metrics['f1_weighted']:.4f}")
        print("="*80)
        
        # Print detailed classification report
        print("\n" + "="*80)
        print("=== Per-Class Metrics ===")
        print("="*80)
        for label in labels:
            if label in report:
                metrics_per_class = report[label]
                print(f"{label:30s} | P: {metrics_per_class['precision']:.3f} | R: {metrics_per_class['recall']:.3f} | F1: {metrics_per_class['f1-score']:.3f} | Support: {int(metrics_per_class['support'])}")
        print("="*80 + "\n")
        
        # Print confusion matrix
        print("Confusion Matrix:")
        print(conf_matrix_df)
        print("\n")
        
        # Print book-level statistics
        print("=== Book-Level Statistics ===")
        for book_stat in book_stats:
            print(f"{book_stat['book_name']:40s} | Accuracy: {book_stat['score']:6.2%} ({book_stat['correct_matches']:4d}/{book_stat['total_matches']:4d})")
        
        print("="*80 + "\n")
    
    def _log_to_mlflow(
        self,
        prompt_name: str,
        all_matches_df: pd.DataFrame,
        book_stats_df: pd.DataFrame,
        conf_matrix_df: pd.DataFrame,
        classification_report: Dict[str, Any],
        metrics: Dict[str, Any],
    ) -> None:
        """
        Log text extraction evaluation results to MLflow.
        
        Note: This runs inside the MLflow run context started by BaseEvaluator.run()
        """
        # Get current timestamp in CEST
        time_now_cest = datetime.now(ZoneInfo("Europe/Paris"))
        
        # Set MLflow tags (within the existing run)
        mlflow.set_tag("prompt_name", prompt_name)
        mlflow.set_tag("timestamp_cest", time_now_cest.isoformat())
        
        # Log all metrics
        mlflow.log_metric("accuracy", metrics["accuracy"])
        mlflow.log_metric("precision_macro", metrics["precision_macro"])
        mlflow.log_metric("recall_macro", metrics["recall_macro"])
        mlflow.log_metric("f1_macro", metrics["f1_macro"])
        mlflow.log_metric("precision_weighted", metrics["precision_weighted"])
        mlflow.log_metric("recall_weighted", metrics["recall_weighted"])
        mlflow.log_metric("f1_weighted", metrics["f1_weighted"])
        mlflow.log_metric("total_matches", metrics["total_matches"])
        mlflow.log_metric("valid_matches", metrics["valid_matches"])
        mlflow.log_metric("num_books", metrics["num_books"])
        
        # Try to log artifacts (may fail if Azure Blob Storage auth is not configured)
        try:
            # Log tables
            mlflow.log_table(all_matches_df, "results/all_pages_combined.json")
            mlflow.log_table(book_stats_df, "results/book_level_stats.json")
            mlflow.log_table(conf_matrix_df.reset_index(), "results/confusion_matrix.json")
            
            # Log classification report
            mlflow.log_dict(classification_report, "results/classification_report.json")
            
            # Save and log CSV artifact
            artifact_path = self.output_dir / "artifacts"
            artifact_path.mkdir(exist_ok=True)
            csv_path = artifact_path / f"all_matches_{time_now_cest.strftime('%Y%m%d_%H%M%S')}.csv"
            all_matches_df.to_csv(csv_path, index=False)
            mlflow.log_artifact(str(csv_path), artifact_path="evaluation")
            
            print("✓ MLflow artifacts logged successfully")
        except Exception as e:
            print(f"⚠ Warning: Failed to log artifacts to MLflow (metrics were logged successfully): {type(e).__name__}")
            print(f"  This is likely due to Azure Blob Storage authentication issues.")
