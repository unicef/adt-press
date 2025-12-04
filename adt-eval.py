#!/usr/bin/env python3
"""ADT Evaluation Tool

A general-purpose evaluation framework for testing various ADT Press components.

Usage:
    uv run adt-eval                                    # Run all tasks
    uv run adt-eval tasks=[text_translation]          # Run specific task
    uv run adt-eval tasks=[text_translation] eval.limit=50  # Limit to first 50

Available tasks:
    - text_translation: Evaluate translation accuracy
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from omegaconf import OmegaConf

from adt_eval.text_type import TextTypeEvaluator  # noqa: F401 (kept for future use)
from adt_eval.text_translation import TextTranslationEvaluator

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.traceback import install as install_rich_traceback
import logging

# ---------------------------------------------------------------------------
# Rich + logging setup
# ---------------------------------------------------------------------------

console = Console()

# Install rich tracebacks globally
install_rich_traceback(show_locals=False)

# Configure logging once, with RichHandler
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Registry of available evaluators
# ---------------------------------------------------------------------------

EVALUATORS: Dict[str, Any] = {
    "text_translation": TextTranslationEvaluator,
    # "text_type": TextTypeEvaluator,  # enable when ready
}

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------


def load_config() -> Dict[str, Any]:
    """Load configuration with command-line overrides."""
    # Load environment variables first
    load_dotenv()

    # Register custom env resolver for cleaner syntax
    if not OmegaConf.has_resolver("env"):
        OmegaConf.register_new_resolver("env", lambda var: os.getenv(var))

    # Load main config
    main_config_path = Path("config/config.yaml")
    if not main_config_path.exists():
        raise FileNotFoundError(f"Main config file not found: {main_config_path}")

    main_config = OmegaConf.load(main_config_path)

    # Load evaluation config
    eval_config_path = Path("config/eval_config.yaml")
    if not eval_config_path.exists():
        raise FileNotFoundError(f"Evaluation config file not found: {eval_config_path}")

    eval_config = OmegaConf.load(eval_config_path)

    # Merge configs (eval config takes precedence)
    config = OmegaConf.merge(main_config, eval_config)

    # Make sure command line arguments are strictly validated
    OmegaConf.set_struct(config, True)

    # Apply command-line overrides using OmegaConf
    cli_config = OmegaConf.from_cli()
    config = OmegaConf.merge(config, cli_config)

    # Resolve interpolations to a plain dict
    config_dict: Dict[str, Any] = OmegaConf.to_container(config, resolve=True)

    return config_dict


def get_tasks_to_run(config: Dict[str, Any]) -> List[str]:
    """Determine which tasks to run based on configuration."""
    tasks_to_run = config.get("tasks", [])
    selected_task = config.get("task", "")

    # If empty list, check if single task is specified
    if not tasks_to_run and selected_task:
        tasks_to_run = [selected_task]

    # Default: if nothing specified, run all known tasks
    if not tasks_to_run:
        tasks_to_run = list(EVALUATORS.keys())

    # Validate that all requested tasks exist
    invalid_tasks = [task for task in tasks_to_run if task not in EVALUATORS]
    if invalid_tasks:
        console.print(
            f"[red]Error:[/red] Unknown task(s): [bold]{', '.join(invalid_tasks)}[/bold]"
        )
        console.print(f"Available tasks: [cyan]{', '.join(EVALUATORS.keys())}[/cyan]")
        sys.exit(1)

    return tasks_to_run


def get_task_config(base_config: Dict[str, Any], task: str) -> Dict[str, Any]:
    """Extract task-specific configuration."""
    if task not in base_config["eval"]["task_configs"]:
        raise ValueError(f"Task '{task}' not found in eval_config.yaml")

    return base_config["eval"]["task_configs"][task]


# ---------------------------------------------------------------------------
# Task runner
# ---------------------------------------------------------------------------


async def run_task(
    task: str,
    global_config: Dict[str, Any],
    output_dir: Path,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], Dict[str, Any]]:
    """Run a single evaluation task and return (results, metrics, run_info)."""

    task_config = get_task_config(global_config, task)
    evaluator_class = EVALUATORS[task]
    evaluator = evaluator_class(global_config, task_config, output_dir)

    # Run the evaluator in a background thread (it's synchronous)
    await asyncio.to_thread(evaluator.run)

    # After run() finishes, we expect evaluator to have .results and .metrics
    results: List[Dict[str, Any]] = getattr(evaluator, "results", [])
    metrics: Dict[str, Any] = getattr(evaluator, "metrics", {})

    # Try to get MLflow run info
    run_info: Dict[str, Any] = {}
    eval_results = getattr(evaluator, "experiment_run_results", None)
    if eval_results is not None:
        run_id = getattr(eval_results, "run_id", None)
        experiment_id = evaluator.experiment_run_cfg.get("experiment_id")
        if run_id and experiment_id:
            run_info = {
                "run_id": run_id,
                "experiment_id": experiment_id,
            }

    return results, metrics, run_info


# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------


def print_run_header(label: str, tasks_to_run: List[str], output_dir: Path) -> None:
    console.rule("[bold cyan]ADT Evaluation[/bold cyan]")
    console.print(
        Panel.fit(
            f"[bold]Label:[/bold] [yellow]{label}[/yellow]\n"
            f"[bold]Tasks:[/bold] {', '.join(tasks_to_run)}\n"
            f"[bold]Output directory:[/bold] {output_dir}",
            border_style="cyan",
        )
    )


def print_overall_summary(
    tasks_to_run: List[str],
    all_metrics: Dict[str, Dict[str, Any]],
    output_dir: Path,
) -> None:
    console.rule("[bold green]✨ All evaluations complete ✨[/bold green]")

    # Metrics table
    table = Table(title="Evaluation Summary", show_lines=True)
    table.add_column("Task", style="cyan", no_wrap=True)
    table.add_column("Score", style="bold")
    table.add_column("Other Metrics", style="dim")

    for task in tasks_to_run:
        metrics = all_metrics.get(task, {}) or {}
        score = metrics.get("score", "–")

        # Pack other metrics into a simple string, excluding "score"
        other_items = [
            f"{k}={v}"
            for k, v in metrics.items()
            if k != "score"
        ]
        other_str = ", ".join(other_items) if other_items else ""

        if isinstance(score, (int, float)):
            score_display = f"{score:.3f}"
        else:
            score_display = str(score)

        table.add_row(task, score_display, other_str)

    console.print(table)
    console.print(
        Panel.fit(
            f"[bold]Reports generated in:[/bold] [green]{output_dir}[/green]",
            border_style="cyan",
        )
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main():
    """Main entry point."""
    # Load configuration with CLI overrides
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        console.print_exception()
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error while loading configuration:[/red] {e}")
        console.print_exception()
        sys.exit(1)

    # Determine tasks to run
    tasks_to_run = get_tasks_to_run(config)

    # Setup output directory
    label = config.get("label", "default")
    output_dir = Path("output") / label

    print_run_header(label, tasks_to_run, output_dir)

    # Run evaluations
    all_results: Dict[str, List[Dict[str, Any]]] = {}
    all_metrics: Dict[str, Dict[str, Any]] = {}
    all_runs: Dict[str, Dict[str, Any]] = {}

    try:
        for task in tasks_to_run:
            console.print(
                f"\n[bold cyan]▶ Running task:[/bold cyan] [yellow]{task}[/yellow]"
            )
            console.print(f"[dim]Running {task} evaluation...[/dim]")

            results, metrics, run_info = await run_task(task, config, output_dir)

            all_results[task] = results
            all_metrics[task] = metrics
            all_runs[task] = run_info

            score = metrics.get("score")
            if isinstance(score, (int, float)):
                console.print(
                    f"[green]✔ {task}[/green]: score [bold]{score:.3f}[/bold]"
                )
            else:
                console.print(
                    f"[green]✔ {task}[/green]: [dim]score not available[/dim]"
                )

            # Print MLflow info if we have it
            if run_info:
                mlflow_url = (
                    f"http://host.docker.internal:5000/#/experiments/"
                    f"{run_info['experiment_id']}/evaluation-runs?"
                    f"selectedRunUuid={run_info['run_id']}"
                )
                console.print(
                    Panel.fit(
                        f"[bold]MLflow Run ID:[/bold] {run_info['run_id']}\n"
                        f"[bold]Experiment ID:[/bold] {run_info['experiment_id']}\n\n"
                        f"[bold green]View results:[/bold green] {mlflow_url}",
                        title=f"MLflow ({task})",
                        border_style="green",
                    )
                )

        # Final summary
        print_overall_summary(tasks_to_run, all_metrics, output_dir)

    except Exception as e:
        console.print(f"[red]Evaluation failed:[/red] {e}")
        console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
