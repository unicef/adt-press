import os

import structlog
from hamilton.function_modifiers import cache
from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel

from adt_press.llm.language_detection import detect_input_language
from adt_press.models.config import (
    CropPromptConfig,
    HTMLPromptConfig,
    LayoutType,
    MetadataPromptConfig,
    PageRangeConfig,
    PromptConfig,
    RenderPromptConfig,
    RenderStrategy,
    SpeechPromptConfig,
)
from adt_press.models.text import PageTexts
from adt_press.utils.config import prompt_config_with_model
from adt_press.utils.file import calculate_file_hash
from adt_press.utils.html import TemplateConfig
from adt_press.utils.sync import run_async_task

log = structlog.get_logger(__name__)


def config() -> DictConfig:  # pragma: no cover
    assert False, "This function should not be called directly. Use the config from the pipeline instead."


def template_config(run_output_dir_config: str) -> TemplateConfig:
    return TemplateConfig(output_dir=run_output_dir_config)


def pdf_path_config(config: DictConfig) -> str:
    return str(config["pdf_path"])


def custom_plate_path_config(config: DictConfig) -> str:
    return str(config.get("custom_plate_path", ""))


def _clean_language_override(language_value: str | None) -> str | None:
    if language_value is None:
        return None
    return str(language_value).strip().lower()


def pdf_text_sample(pdf_texts: dict[str, PageTexts], max_chars: int = 2000) -> str:
    collected: list[str] = []
    total_chars = 0

    for page_id in sorted(pdf_texts.keys()):
        page_texts = pdf_texts[page_id]
        for group in page_texts.groups:
            for text in group.texts:
                snippet = text.text.strip()
                if not snippet:
                    continue

                collected.append(snippet)
                total_chars += len(snippet)
                if total_chars >= max_chars:
                    return "\n".join(collected)

    return "\n".join(collected)


def input_language_config(
    config: DictConfig,
    language_detection_prompt_config: PromptConfig,
    pdf_text_sample: str,
) -> str:
    override_value = OmegaConf.select(config, "input_language", default=None)
    override = _clean_language_override(override_value)
    if override:
        return override

    if not pdf_text_sample.strip():
        raise RuntimeError("language detection failed; pdf has no text!")

    try:
        response = run_async_task(lambda: detect_input_language(pdf_text_sample, language_detection_prompt_config))
        confidence = getattr(response, "confidence", None)
        log.info("input language detected automatically", language=response.language_code, confidence=confidence)
        return response.language_code
    except Exception:  # pragma: no cover - fallback path
        raise RuntimeError("language detection failed; please specify `input_language` configuration parameter")


def plate_language_config(config: DictConfig, input_language_config: str) -> str:
    plate_override_value = OmegaConf.select(config, "plate_language", default=None)
    plate_override = _clean_language_override(plate_override_value)
    if plate_override:
        return plate_override

    log.info("plate language defaulted to input language", language=input_language_config)
    return input_language_config


def output_languages_config(config: DictConfig, input_language_config: str) -> list[str]:
    raw_languages = OmegaConf.select(config, "output_languages", default=None)
    sequence: list[str | None] = []
    if raw_languages is not None:
        container = OmegaConf.to_container(raw_languages, resolve=True)
        if isinstance(container, list):
            for item in container:
                sequence.append(str(item) if item is not None else None)
        else:
            raise RuntimeError("output languages config must be a list; please specify `output_languages` configuration parameter")
    cleaned_languages: list[str] = []

    if sequence:
        for language in sequence:
            cleaned = _clean_language_override(language)
            if cleaned:
                cleaned_languages.append(cleaned)
            else:
                raise RuntimeError("output languages config must be a list; please specify `output_languages` configuration parameter")

    if not cleaned_languages:
        cleaned_languages = [input_language_config]
        log.info("output languages defaulted to input language", languages=cleaned_languages)

    return cleaned_languages


def label_config(config: DictConfig) -> str:
    return str(config["label"])


@cache(behavior="recompute")
def run_output_dir_config(config: DictConfig) -> str:
    run_output_dir = str(config["run_output_dir"])
    os.makedirs(run_output_dir, exist_ok=True)
    return run_output_dir


def pdf_title_config(config: DictConfig, label_config: str) -> str:
    return str(config.get("pdf_title", label_config))


@cache(behavior="recompute")
def pdf_hash_config(pdf_path_config: str) -> str:
    return calculate_file_hash(pdf_path_config)


def page_range_config(config: DictConfig) -> PageRangeConfig:
    return PageRangeConfig.model_validate(config.get("page_range", {}))


def page_grouping_config(config: DictConfig) -> str:
    return str(config.get("page_grouping", "single"))


@cache(behavior="recompute")
def layout_types_config(config: DictConfig) -> dict[str, LayoutType]:
    types = dict[str, LayoutType]()
    for name, layout_type in config["layout_types"].items():
        params = dict(layout_type)
        params["name"] = name
        types[name] = LayoutType.model_validate(params)
    return types


@cache(behavior="recompute")
def render_strategy_config(config: DictConfig, render_strategies_config: dict[str, RenderStrategy]) -> str:
    strategy = str(config["render_strategy"])
    if strategy != "dynamic" and strategy not in render_strategies_config:
        raise ValueError(f"Unknown render strategy: {strategy}")
    return strategy


@cache(behavior="recompute")
def render_strategies_config(config: DictConfig) -> dict[str, RenderStrategy]:
    strategies = dict[str, RenderStrategy]()
    for name, strategy in config["render_strategies"].items():
        params = dict(strategy)
        params["name"] = name
        strategies[name] = RenderStrategy.model_validate(params)
    return strategies


@cache(behavior="recompute")
def default_model_config(config: DictConfig) -> str:
    return str(config["default_model"])


@cache(behavior="recompute")
def caption_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(prompt_config_with_model(config["prompts"]["caption"], config["default_model"]))


@cache(behavior="recompute")
def language_detection_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(prompt_config_with_model(config["prompts"]["language_detection"], config["default_model"]))


@cache(behavior="recompute")
def crop_prompt_config(config: DictConfig) -> CropPromptConfig:
    return CropPromptConfig.model_validate(prompt_config_with_model(config["prompts"]["crop"], config["default_model"]))


@cache(behavior="recompute")
def meaningfulness_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(prompt_config_with_model(config["prompts"]["meaningfulness"], config["default_model"]))


@cache(behavior="recompute")
def text_extraction_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(prompt_config_with_model(config["prompts"]["text_extraction"], config["default_model"]))


@cache(behavior="recompute")
def metadata_extraction_prompt_config(config: DictConfig) -> MetadataPromptConfig:
    return MetadataPromptConfig.model_validate(prompt_config_with_model(config["prompts"]["metadata_extraction"], config["default_model"]))


@cache(behavior="recompute")
def page_sectioning_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(prompt_config_with_model(config["prompts"]["page_sectioning"], config["default_model"]))


@cache(behavior="recompute")
def section_explanation_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(prompt_config_with_model(config["prompts"]["section_explanation"], config["default_model"]))


@cache(behavior="recompute")
def text_translation_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(prompt_config_with_model(config["prompts"]["text_translation"], config["default_model"]))


@cache(behavior="recompute")
def glossary_translation_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(prompt_config_with_model(config["prompts"]["glossary_translation"], config["default_model"]))


@cache(behavior="recompute")
def section_glossary_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(prompt_config_with_model(config["prompts"]["section_glossary"], config["default_model"]))


@cache(behavior="recompute")
def text_easy_read_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(prompt_config_with_model(config["prompts"]["text_easy_read"], config["default_model"]))


@cache(behavior="recompute")
def speech_prompt_config(config: DictConfig) -> PromptConfig:
    return SpeechPromptConfig.model_validate(prompt_config_with_model(config["prompts"]["speech_generation"], config["default_model"]))


@cache(behavior="recompute")
def section_metadata_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(prompt_config_with_model(config["prompts"]["section_metadata"], config["default_model"]))


@cache(behavior="recompute")
def web_generation_html_prompt_config(config: DictConfig) -> HTMLPromptConfig:
    return HTMLPromptConfig.model_validate(prompt_config_with_model(config["prompts"]["web_generation_html"], config["default_model"]))


@cache(behavior="recompute")
def web_generation_rows_prompt_config(config: DictConfig) -> RenderPromptConfig:
    return RenderPromptConfig.model_validate(prompt_config_with_model(config["prompts"]["web_generation_rows"], config["default_model"]))


@cache(behavior="recompute")
def web_generation_two_column_prompt_config(config: DictConfig) -> RenderPromptConfig:
    return RenderPromptConfig.model_validate(
        prompt_config_with_model(config["prompts"]["web_generation_two_column"], config["default_model"])
    )


def image_config(config: DictConfig) -> DictConfig:
    return DictConfig(config.get("image_filters", {}))


def strategy_config(config: DictConfig) -> dict[str, str]:
    return dict[str, str](
        {
            "caption_strategy": config["caption_strategy"],
            "crop_strategy": config["crop_strategy"],
            "glossary_strategy": config["glossary_strategy"],
            "explanation_strategy": config["explanation_strategy"],
            "easy_read_strategy": config["easy_read_strategy"],
            "speech_strategy": config["speech_strategy"],
        }
    )


class ImageSizeFilterConfig(BaseModel):
    max_side: int = 500
    min_side: int = 50


def image_size_filter_config(image_config: DictConfig) -> ImageSizeFilterConfig:
    return ImageSizeFilterConfig.model_validate(image_config.get("size", {}))


class BlankImageFilterConfig(BaseModel):
    threshold: int = 2


def blank_image_filter_config(image_config: DictConfig) -> BlankImageFilterConfig:
    return BlankImageFilterConfig.model_validate(image_config.get("blank", {}))


def pruned_text_types_config(config: DictConfig) -> list[str]:
    return list[str](config.get("text_filters", {}).get("pruned_text_types", []))


def pruned_section_types_config(config: DictConfig) -> list[str]:
    return list[str](config.get("section_filters", {}).get("pruned_section_types", []))
