import os
import shutil
from typing import Any, Dict

import litellm
import structlog
from hamilton import driver, registry, telemetry
from hamilton.lifecycle import NodeExecutionHook
from omegaconf import DictConfig

from adt_press.nodes import config_nodes, image_nodes, pdf_nodes, plate_nodes, report_nodes, section_nodes, speech_nodes, web_nodes

registry.disable_autoload()
telemetry.disable_telemetry()

log = structlog.get_logger()


modules = [
    config_nodes,
    image_nodes,
    report_nodes,
    pdf_nodes,
    section_nodes,
    web_nodes,
    plate_nodes,
    speech_nodes,
]


class NodeHook(NodeExecutionHook):
    def run_before_node_execution(
        self,
        *,
        node_name: str,
        node_tags: Dict[str, Any],
        node_kwargs: Dict[str, Any],
        node_return_type: type,
        task_id: str | None,
        run_id: str,
        node_input_types: Dict[str, Any],
        **future_kwargs: Any,
    ):
        log.info("node evaluating", node=node_name)

    def run_after_node_execution(
        self,
        *,
        node_name: str,
        node_tags: Dict[str, Any],
        node_kwargs: Dict[str, Any],
        node_return_type: type,
        result: Any,
        error: Exception | None,
        success: bool,
        task_id: str | None,
        run_id: str,
        **future_kwargs: Any,
    ):
        log.info("node result", node=node_name, success=success, result=result, error=error)


def run_pipeline(config: DictConfig) -> None:
    cache_path = os.path.join(config["run_output_dir"], "cache")
    clear_cache = config.get("clear_cache", False)
    if clear_cache:
        shutil.rmtree(cache_path, ignore_errors=True)

    # we pass through all strategies as configs to the driver
    driver_config = {}
    for key, value in config.items():
        if str(key).endswith("_strategy"):
            driver_config[key] = value

    dr = (
        driver.Builder()
        .with_config(driver_config)
        .with_modules(*modules)
        .with_cache(path=cache_path)
        .with_adapters(NodeHook())
        .build()
    )  # fmt: off

    # print available models
    if config.get("print_available_models", False):
        print("Available models:")
        for model in litellm.get_valid_models():
            print(f"- {model}")

    # Execute nodes in sequence to ensure reports are generated even if later steps fail
    nodes_to_execute = ["report_pages", "plate_report", "glossary_report", "web_report", "report_index"]

    dr.execute(nodes_to_execute, overrides={"config": config})

    # output our run graph as a png
    dr.cache.view_run(output_file_path=f"{config['run_output_dir']}/run.png")
