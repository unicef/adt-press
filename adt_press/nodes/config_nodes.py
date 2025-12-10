import os

from hamilton.function_modifiers import cache
from hamilton.function_modifiers import config as when_config
from omegaconf import DictConfig
from pydantic import BaseModel

from adt_press.models.config import (
    CropPromptConfig,
    HTMLPromptConfig,
    MetadataPromptConfig,
    PageRangeConfig,
    PromptConfig,
    RenderPromptConfig,
    RenderStrategy,
    SectionType,
    SpeechPromptConfig,
)
from adt_press.utils.config import prompt_config_with_model
from adt_press.utils.file import calculate_file_hash
from adt_press.utils.html import TemplateConfig


def config() -> DictConfig:  # pragma: no cover
    assert False, "This function should not be called directly. Use the config from the pipeline instead."


def template_config(run_output_dir_config: str) -> TemplateConfig:
    return TemplateConfig(output_dir=run_output_dir_config)


def pdf_path_config(config: DictConfig) -> str:
    return str(config["pdf_path"])


def custom_plate_path_config(config: DictConfig) -> str:
    return str(config.get("custom_plate_path", ""))


def input_language_config(config: DictConfig) -> str:
    return str(config.get("input_language", "en"))


def plate_language_config(config: DictConfig) -> str:
    return str(config.get("plate_language", "en"))


def output_languages_config(config: DictConfig) -> list[str]:
    return list[str](config["output_languages"])


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
