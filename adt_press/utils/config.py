

from omegaconf import DictConfig, ListConfig, OmegaConf


def conf_to_object(value: DictConfig | ListConfig) -> dict | list:
    return {} if value is None else OmegaConf.to_container(value, resolve=True)