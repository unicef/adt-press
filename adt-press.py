import hydra
import litellm
from hamilton import driver, registry
from omegaconf import DictConfig

from adt_press.nodes import config_nodes, pdf_nodes, report_nodes

registry.disable_autoload()

modules = [
    config_nodes,
    pdf_nodes,
    report_nodes,
]


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(config: DictConfig) -> None:
    cache_args = {"recompute": True} if config.get("clear_cache", False) else {}
    dr = (
        driver.Builder()
        .with_modules(*modules)
        .with_cache(**cache_args)
        .build()
    )  # fmt: off

    # print available models
    print("Available models:")
    for model in litellm.get_valid_models():
        print(f"- {model}")

    dr.execute(["report_index"], overrides={"config": config})

    dr.cache.view_run(output_file_path=f"{config['output_dir']}/run.png")


if __name__ == "__main__":
    main()
