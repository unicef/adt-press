import base64
from typing import Any

import ftfy
from pydantic import BaseModel, model_validator


def base64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


# ftfy doesn't deal with m dashes, so we add some manual fixes
ENCODING_FIXES = str.maketrans({"–": "-", "‐": "-"})


def _clean(obj: Any) -> Any:
    if isinstance(obj, str):
        fixed = ftfy.fix_text(obj, normalization="NFKC")
        fixed = fixed.translate(ENCODING_FIXES)
        return fixed
    if isinstance(obj, list):
        return [_clean(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    return obj


class CleanTextBaseModel(BaseModel):
    """Mixin for base models used with the LLM to clean up text fields to not include spurious unicode."""

    @model_validator(mode="before")
    @classmethod
    def _clean_text(cls, v):
        return _clean(v)
