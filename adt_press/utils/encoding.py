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


EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # symbols and pictographs
    "\U0001f680-\U0001f6ff"  # transport and map symbols
    "\U0001f700-\U0001f77f"  # alchemical symbols
    "\U0001f780-\U0001f7ff"  # geometric shapes extended
    "\U0001f800-\U0001f8ff"  # supplemental arrows-c
    "\U0001f900-\U0001f9ff"  # supplemental symbols and pictographs
    "\U0001fa00-\U0001fa6f"  # chess symbols
    "\U0001fa70-\U0001faff"  # symbols and pictographs extended-a
    "\U00002702-\U000027b0"  # dingbats
    "\U000024c2-\U0001f251"  # enclosed characters
    "]+"
)


def starts_with_emoji(text: str) -> bool:
    """Return True when the provided string begins with an emoji."""
    if not text:
        return False

    return bool(EMOJI_PATTERN.match(text))


def strip_emojis(text: str) -> str:
    """Remove all emoji codepoints from the provided string."""
    if not text:
        return text

    return EMOJI_PATTERN.sub("", text)
