from omegaconf import DictConfig, OmegaConf

from adt_press.pipeline import run_pipeline


def main() -> None:
    cli_config = OmegaConf.from_cli()
    file_config = OmegaConf.load("config/config.yaml")

    # Enable struct mode to validate CLI parameters against config schema
    OmegaConf.set_struct(file_config, True)

    config = DictConfig(OmegaConf.merge(file_config, cli_config))
    print(OmegaConf.to_yaml(config))

    run_pipeline(config)


if __name__ == "__main__":  # pragma: no cover
    main()
