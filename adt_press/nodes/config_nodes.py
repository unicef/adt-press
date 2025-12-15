import os

import structlog
from hamilton.function_modifiers import cache
from hamilton.function_modifiers import config as when_config
from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel

from adt_press.llm.language_detection import detect_input_language
from adt_press.models.config import (
    CropPromptConfig,
    HTMLPromptConfig,
    MetadataPromptConfig,
    PageRangeConfig,
    PromptConfig,
    QuizPromptConfig,
    RenderPromptConfig,
    RenderStrategy,
    SectionType,
    SpeechPromptConfig,
)
from adt_press.models.text import PageTexts
from adt_press.utils.config import prompt_config_with_model
from adt_press.utils.file import calculate_file_hash
from adt_press.utils.html import TemplateConfig
from adt_press.utils.languages import CUSTOM_LANGUAGE_MAP, LANGUAGE_MAP
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


SUPPORTED_LANGUAGE_CODES = set(LANGUAGE_MAP.keys()) | set(CUSTOM_LANGUAGE_MAP.keys())


def _clean_language_override(language_value: str | None) -> str | None:
    if language_value is None:
        return None
    return str(language_value).strip().lower()


def _validate_language_code(language_code: str, *, field_name: str) -> None:
    if language_code not in SUPPORTED_LANGUAGE_CODES:
        raise ValueError(f"{field_name} unsupported language code: {language_code!r}")


def _flatten_output_languages(raw_languages: object) -> list[str | None]:
    sequence: list[str | None] = []
    if raw_languages is None:
        return sequence

    if OmegaConf.is_list(raw_languages) or isinstance(raw_languages, (list, tuple)):
        for item in raw_languages:
            if item is None:
                sequence.append(None)
                continue
            entry = str(item)
            if "," in entry:
                raise ValueError(
                    f"output_languages contains a comma-separated entry {entry!r} inside a list. "
                    "Use a scalar string like 'en,es' or a list like ['en','es']."
                )
            sequence.append(entry)
        return sequence

    if isinstance(raw_languages, str):
        raw_str = raw_languages.strip()
        if raw_str in ("", "???"):
            return sequence
        if "," in raw_str:
            parts = [part.strip() for part in raw_str.split(",")]
            if any(not part for part in parts):
                raise ValueError(f"output_languages contains an empty language code in {raw_languages!r}")
            sequence.extend(parts)
        else:
            sequence.append(raw_str)
        return sequence

    raise TypeError(
        "output_languages must be a list of language codes or a comma-separated string; "
        f"got {type(raw_languages).__name__}"
    )


def _coerce_output_language(language_value: str | None, input_language_code: str) -> str:
    if language_value is None:
        if not input_language_code:
            raise ValueError(
                "output_languages contained a null entry, but input_language could not be determined. "
                "Specify input_language or explicit output_languages."
            )
        return input_language_code

    cleaned = _clean_language_override(language_value)
    if not cleaned:
        raise ValueError(f"output_languages contains an empty language code: {language_value!r}")
    if cleaned not in SUPPORTED_LANGUAGE_CODES:
        raise ValueError(f"output_languages unsupported language code: {cleaned!r}")
    return cleaned


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
        if "," in override:
            raise ValueError(
                f"input_language must be a single language code like 'en'; got {override!r}. Use output_languages for multiple languages."
            )
        _validate_language_code(override, field_name="input_language")
        return override

    if not pdf_text_sample.strip():
        raise ValueError("language detection failed; pdf has no text!")

    try:
        response = run_async_task(lambda: detect_input_language(pdf_text_sample, language_detection_prompt_config))
        confidence = getattr(response, "confidence", None)
        log.info("input language detected automatically", language=response.language_code, confidence=confidence)
        return response.language_code
    except Exception:  # pragma: no cover - fallback path
        raise ValueError("language detection failed; please specify `input_language` configuration parameter")


def plate_language_config(config: DictConfig, input_language_config: str) -> str:
    plate_override_value = OmegaConf.select(config, "plate_language", default=None)
    plate_override = _clean_language_override(plate_override_value)
    if plate_override:
        return plate_override

    log.info("plate language defaulted to input language", language=input_language_config)
    return input_language_config


def output_languages_config(config: DictConfig, input_language_config: str) -> list[str]:
    raw_languages = OmegaConf.select(config, "output_languages", default=None)
    sequence = _flatten_output_languages(raw_languages)
    cleaned_languages: list[str] = []
    for language in sequence:
        cleaned = _coerce_output_language(language, input_language_config)
        if cleaned not in cleaned_languages:
            cleaned_languages.append(cleaned)

    if not cleaned_languages:
        _validate_language_code(input_language_config, field_name="input_language")
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
def section_types_config(config: DictConfig, default_render_strategy_config: str) -> dict[str, SectionType]:
    types = dict[str, SectionType]()
    for name, section_type in config["section_types"].items():
        params = dict(section_type)
        params["name"] = name
        # Use default_render_strategy if not specified in section_type
        if "render_strategy" not in params:
            params["render_strategy"] = default_render_strategy_config
        types[name] = SectionType.model_validate(params)
    return types


@cache(behavior="recompute")
def default_render_strategy_config(config: DictConfig) -> str:
    return str(config.get("default_render_strategy", "html"))


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
def quiz_prompt_config(config: DictConfig) -> QuizPromptConfig:
    return QuizPromptConfig.model_validate(prompt_config_with_model(config["prompts"]["section_quiz"], config["default_model"]))


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
def activity_answers_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(prompt_config_with_model(config["prompts"]["activity_answers"], config["default_model"]))


@cache(behavior="recompute")
@when_config.when(activity_strategy="llm")
def activity_prompts_config__llm(config: DictConfig) -> dict[str, HTMLPromptConfig]:
    """Load activity-specific prompt configs into a dictionary keyed by section type."""
    activity_types = [
        "activity_sorting",
        "activity_matching",
        "activity_fill_in_a_table",
        "activity_true_false",
        "activity_open_ended_answer",
        "activity_fill_in_the_blank",
        "activity_multiple_choice",
    ]

    activity_configs = {}
    for activity_type in activity_types:
        if activity_type in config["prompts"]:
            activity_configs[activity_type] = HTMLPromptConfig.model_validate(
                prompt_config_with_model(config["prompts"][activity_type], config["default_model"])
            )

    return activity_configs


@cache(behavior="recompute")
@when_config.when(activity_strategy="none")
def activity_prompts_config__none(config: DictConfig) -> dict[str, HTMLPromptConfig]:
    """Return empty dict when activity generation is disabled."""
    return {}


@cache(behavior="recompute")
@when_config.when(activity_strategy="llm")
def activity_answers_prompts_config__llm(config: DictConfig) -> dict[str, PromptConfig]:
    """Load activity-specific answer generation prompt configs into a dictionary keyed by section type."""
    activity_types = [
        "activity_sorting",
        "activity_matching",
        "activity_fill_in_a_table",
        "activity_true_false",
        "activity_fill_in_the_blank",
        "activity_multiple_choice",
    ]

    answer_configs = {}

    for activity_type in activity_types:
        answer_key = f"{activity_type}_answers"
        if answer_key in config["prompts"]:
            answer_configs[activity_type] = PromptConfig.model_validate(
                prompt_config_with_model(config["prompts"][answer_key], config["default_model"])
            )

    return answer_configs


@cache(behavior="recompute")
@when_config.when(activity_strategy="none")
def activity_answers_prompts_config__none(config: DictConfig) -> dict[str, PromptConfig]:
    """Return empty dict when activity answer generation is disabled."""
    return {}


@cache(behavior="recompute")
def speech_prompt_config(config: DictConfig) -> PromptConfig:
    return SpeechPromptConfig.model_validate(prompt_config_with_model(config["prompts"]["speech_generation"], config["default_model"]))


@cache(behavior="recompute")
def web_generation_html_prompt_config(config: DictConfig) -> HTMLPromptConfig:
    return HTMLPromptConfig.model_validate(prompt_config_with_model(config["prompts"]["web_generation_html"], config["default_model"]))


@cache(behavior="recompute")
def web_generation_activity_prompt_config(config: DictConfig) -> HTMLPromptConfig:
    return HTMLPromptConfig.model_validate(prompt_config_with_model(config["prompts"]["web_generation_activity"], config["default_model"]))


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
            "activity_strategy": config["activity_strategy"],
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
