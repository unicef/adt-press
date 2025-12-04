from __future__ import annotations

from pathlib import Path
from typing import Any

from slugify import slugify


def clean_label_value(label_value: Any | None) -> str | None:
    if label_value is None:
        return None

    normalized = str(label_value).strip()
    if not normalized or normalized == "???":
        return None

    return normalized


def slug_from_pdf_path(pdf_path: str) -> str:
    stem = Path(pdf_path).stem
    slug = slugify(stem, lowercase=True)
    return slug


def ensure_config_label(config, logger=None):
    from omegaconf import OmegaConf  # lazy import to avoid cycles

    label_value = OmegaConf.select(config, "label", default=None)
    cleaned_label = clean_label_value(label_value)
    if cleaned_label:
        return cleaned_label

    pdf_path = str(config["pdf_path"])
    generated_label = slug_from_pdf_path(pdf_path)
    config["label"] = generated_label

    if logger is not None:
        logger.info("config label set automatically", label=generated_label, source=pdf_path)

    return generated_label
