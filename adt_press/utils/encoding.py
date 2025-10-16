import base64
from typing import Any

from ftfy import fix_text
from pydantic import BaseModel, model_validator


def base64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def _clean(obj: Any):
    if isinstance(obj, str):
        return fix_text(obj)
    if isinstance(obj, list):
        return [_clean(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    return obj


class CleanTextMixin(BaseModel):
    """Mixing for base models used with the LLM to clean up text fields to not include spurious unicode."""

    @model_validator(mode="before")
    @classmethod
    def _clean_text(cls, v):
        return _clean(v)
