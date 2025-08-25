from enum import Enum
from typing import Any

from omegaconf import DictConfig, ListConfig, OmegaConf


def conf_to_object(value: DictConfig | ListConfig) -> dict[str | bytes | int | Enum | float | bool, Any] | list[Any] | str | Any | None:
    return {} if value is None else OmegaConf.to_container(value, resolve=True)

def prompt_config_with_model(value: DictConfig, default_model: str) -> DictConfig:
    if value["model"] == "default":
        value["model"] = default_model
    return conf_to_object(value)