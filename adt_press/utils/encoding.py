import base64
import re
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


def starts_with_emoji(text: str) -> bool:
    """Return True when the provided string begins with an emoji."""
    if not text:
        return False

    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols and pictographs
        "\U0001F680-\U0001F6FF"  # transport and map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # geometric shapes extended
        "\U0001F800-\U0001F8FF"  # supplemental arrows-c
        "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "]+"
    )

    return bool(emoji_pattern.match(text))
