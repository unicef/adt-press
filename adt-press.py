import os

from omegaconf import DictConfig, OmegaConf

from adt_press.pipeline import run_pipeline

# never write these flags to our config file
TEMP_FLAGS = ["clear_cache", "print_available_models"]


def main() -> None:
    cli_config = OmegaConf.from_cli()
    default_config = OmegaConf.load("config/config.yaml")

    # Enable struct mode to validate CLI parameters against config schema
    OmegaConf.set_struct(default_config, True)
    default_config = DictConfig(OmegaConf.merge(default_config, cli_config))

    run_output_dir = default_config["run_output_dir"]
    os.makedirs(run_output_dir, exist_ok=True)

    config_path = os.path.join(run_output_dir, "config.yaml")
    if not os.path.exists(config_path):
        # create an empty config file to hold our merged config
        with open(config_path, "w") as f:  # pragma: no cover
            f.write("# Configuration overrides\n")

    file_config = OmegaConf.load(config_path)

    # write our config file out, merging in any new cli options
    output_config = DictConfig(OmegaConf.merge(file_config, cli_config))
    for flag in TEMP_FLAGS:
        if flag in output_config:
            del output_config[flag]
    OmegaConf.save(output_config, config_path)

    # our final config is the merging of the default config, file config and cli config
    config = DictConfig(OmegaConf.merge(default_config, file_config, cli_config))

    # print the final config for debugging
    print("Final configuration:")
    print(OmegaConf.to_yaml(config))

    run_pipeline(config)


if __name__ == "__main__":  # pragma: no cover
    main()
