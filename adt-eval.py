#!/usr/bin/env python3
"""ADT Evaluation Tool

A general-purpose evaluation framework for testing various ADT Press components.

Usage:
    uv run adt-eval                                    # Run all tasks
    uv run adt-eval tasks_to_run=[text_type]     # Run specific task
    uv run adt-eval tasks_to_run=[text_type] eval.limit=50 # Limit to first 50

Available tasks:
    - text_type: Evaluate text type accuracy
"""

import asyncio
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from omegaconf import OmegaConf

from adt_eval.text_type import TextTypeEvaluator
from adt_press.models.config import TemplateConfig
from adt_press.utils.html import render_template

# Registry of available evaluators
EVALUATORS = {
    "text_type": TextTypeEvaluator,
}


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

    # Resolve interpolations
    config = OmegaConf.to_container(config, resolve=True)

    return config


def get_tasks_to_run(config: Dict[str, Any]) -> List[str]:
    """Determine which tasks to run based on configuration."""
    tasks_to_run = config.get("tasks", [])

    # If empty list, run all available tasks
    if not tasks_to_run:
        tasks_to_run = list(EVALUATORS.keys())

    # Validate that all requested tasks exist
    invalid_tasks = [task for task in tasks_to_run if task not in EVALUATORS]
    if invalid_tasks:
        print(f"Error: Unknown tasks: {', '.join(invalid_tasks)}")
        print(f"Available tasks: {', '.join(EVALUATORS.keys())}")
        sys.exit(1)

    return tasks_to_run


def get_task_config(base_config: Dict[str, Any], task: str) -> Dict[str, Any]:
    """Extract task-specific configuration."""
    if task not in base_config["eval"]["task_configs"]:
        raise ValueError(f"Task '{task}' not found in eval_config.yaml")

    return base_config["eval"]["task_configs"][task]


async def run_task(task: str, global_config: Dict[str, Any], output_dir: Path) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run a single evaluation task."""
    task_config = get_task_config(global_config, task)
    evaluator_class = EVALUATORS[task]
    evaluator = evaluator_class(global_config, task_config, output_dir)

    print(f"Running {task} evaluation...")
    return await evaluator.run()


async def main():
    """Main entry point."""
    # Load configuration with CLI overrides
    try:
        config = load_config()
    except FileNotFoundError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)

    # Determine tasks to run
    tasks_to_run = get_tasks_to_run(config)

    # Setup output directory
    output_dir = Path("output") / config["label"]

    print(f"Running evaluation for tasks: {', '.join(tasks_to_run)}")
    print(f"Output directory: {output_dir}")
    print()

    # Run evaluations
    all_results = {}
    all_metrics = {}

    try:
        for task in tasks_to_run:
            results, metrics = await run_task(task, config, output_dir)
            all_results[task] = results
            all_metrics[task] = metrics

            print(f"✓ {task}: {len(results)} cases, {metrics['score']:.1%} score")

        context = {
            "tasks": tasks_to_run,
            "metrics": all_metrics,
            "results": all_results,
        }

        render_template(TemplateConfig(output_dir=str(output_dir)), "eval/index.html", context)
        render_template(TemplateConfig(output_dir=str(output_dir)), "eval/results.txt", context)

        print("\nAll evaluations complete!")
        print(f"Reports generated in: {output_dir}")

    except Exception as e:
        print(f"Evaluation failed: {e}")
        traceback.print_exc()

        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
