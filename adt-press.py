import litellm
from hamilton import driver, registry, telemetry
from omegaconf import OmegaConf

registry.disable_autoload()

from typing import Any, Dict

import structlog
from hamilton.lifecycle import NodeExecutionHook

from adt_press.nodes import config_nodes, pdf_nodes, report_nodes

telemetry.disable_telemetry()

log = structlog.get_logger()

modules = [
    config_nodes,
    pdf_nodes,
    report_nodes,
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


def main() -> None:
    cli_config = OmegaConf.from_cli()
    file_config = OmegaConf.load("config/config.yaml")
    config = OmegaConf.merge(file_config, cli_config)
    print(OmegaConf.to_yaml(config))

    cache_args = {"recompute": True} if config.get("clear_cache", False) else {}

    dr = (
        driver.Builder()
        .with_modules(*modules)
        .with_cache(**cache_args)
        .with_adapters(NodeHook())
        .build()
    )  # fmt: off

    # print available models
    if config.get("print_available_models", False):
        print("Available models:")
        for model in litellm.get_valid_models():
            print(f"- {model}")

    dr.execute(["report_index"], overrides={"config": config})

    # output our run graph as a png
    dr.cache.view_run(output_file_path=f"{config['output_dir']}/run.png")


if __name__ == "__main__":
    main()
