from enum import Enum
from typing import Any

from omegaconf import DictConfig, ListConfig, OmegaConf


def conf_to_object(value: DictConfig | ListConfig) -> dict[str | bytes | int | Enum | float | bool, Any] | list[Any] | str | Any | None:
    return {} if value is None else OmegaConf.to_container(value, resolve=True)
