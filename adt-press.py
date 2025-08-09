import os

from omegaconf import DictConfig, OmegaConf

from adt_press.pipeline import run_pipeline


def main() -> None:
    cli_config = OmegaConf.from_cli()
    default_config = OmegaConf.load("config/config.yaml")

    # Enable struct mode to validate CLI parameters against config schema
    OmegaConf.set_struct(default_config, True)
    config = DictConfig(OmegaConf.merge(default_config, cli_config))

    run_output_dir = config["run_output_dir"]
    os.makedirs(run_output_dir, exist_ok=True)

    config_path = os.path.join(run_output_dir, "config.yaml")

    # if the config exists, read it and merge with our config
    if os.path.exists(config_path): # pragma: no over
        print("Reading config from:", config_path)
        output_config = OmegaConf.load(config_path)

        # rebuild our config for this run - cli > output config > default config
        config = DictConfig(OmegaConf.merge(config, output_config, cli_config))
    else:
        print("Writing config to:", config_path)

        # otherwise, write our cli config to the output directory
        OmegaConf.save(cli_config, config_path)

    # print the final config for debugging
    print("Final configuration:")
    print(OmegaConf.to_yaml(config))

    run_pipeline(config)


if __name__ == "__main__":  # pragma: no cover
    main()
