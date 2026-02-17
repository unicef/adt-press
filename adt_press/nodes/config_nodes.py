import hashlib
import os
import time
from typing import Any, cast

import structlog
import yaml
from hamilton.function_modifiers import cache
from hamilton.function_modifiers import config as when_config
from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel

from adt_press.models.config import (
    CropPromptConfig,
    HTMLPromptConfig,
    MetadataPromptConfig,
    PageRangeConfig,
    PromptConfig,
    QuizPromptConfig,
    RenderPromptConfig,
    RenderStrategy,
    RenderStrategyName,
    RenderType,
    SectionType,
    SectionTypeName,
    SpeechPromptConfig,
    TextGroupType,
    TextGroupTypeName,
    TextType,
    TextTypeName,
)
from adt_press.models.ids import SectionID
from adt_press.utils.config import prompt_config_with_model
from adt_press.utils.file import calculate_file_hash
from adt_press.utils.html import TemplateConfig

log = structlog.get_logger(__name__)


def config() -> DictConfig:  # pragma: no cover
    assert False, "This function should not be called directly. Use the config from the pipeline instead."


def template_config(run_output_dir_config: str) -> TemplateConfig:
    return TemplateConfig(output_dir=run_output_dir_config)


@cache(behavior="recompute")
def bundle_version_config() -> str:
    """Generate a unique cache-busting version for the current build.

    This node is intentionally NOT cached and will generate a new version on every run
    to ensure assets are not cached by browsers between builds.

    Returns:
        8-character MD5 hash based on current timestamp
    """
    return hashlib.md5(str(int(time.time())).encode()).hexdigest()[:8]


def pdf_path_config(config: DictConfig) -> str:
    return str(config["pdf_path"])


def custom_plate_path_config(config: DictConfig) -> str:
    return str(config.get("custom_plate_path", ""))


@cache(behavior="recompute")
def regenerate_sections_config(config: DictConfig) -> list[SectionID]:
    """Returns list of section_ids to regenerate from scratch, or empty list if not regenerating."""
    section_ids = config.get("regenerate_sections", [])
    if not section_ids:
        return []
    return [SectionID(str(sid)) for sid in section_ids]


@cache(behavior="recompute")
def edit_sections_config(config: DictConfig) -> dict[SectionID, str]:
    """Returns dict mapping section_id to annotated image path, or empty dict if not editing.

    Each value should be a path to an annotated screenshot showing desired edits
    via red boxes with white text comments.
    """
    edit_sections = config.get("edit_sections", {})
    if not edit_sections:
        return {}

    # Convert to regular dict with string keys and values
    result = {}
    for k, v in dict(edit_sections).items():
        section_id = SectionID(str(k))
        image_path = str(v)

        # Validate that image file exists
        if not os.path.exists(image_path):
            message = f"Annotated edit image file not found for section {section_id}: {image_path}"
            log.error("edit_image_not_found", section_id=section_id, image_path=image_path, message=message)
            raise FileNotFoundError(message)

        result[section_id] = image_path

    return result


def input_language_config(config: DictConfig) -> str:
    result = OmegaConf.select(config, "input_language", default="auto")
    return str(result) if result is not None else "auto"


def plate_language_config(config: DictConfig) -> str:
    result = OmegaConf.select(config, "plate_language", default="auto")
    return str(result) if result is not None else "auto"


def output_languages_config(config: DictConfig) -> list[str]:
    output_languages = OmegaConf.select(config, "output_languages", default=["auto"])

    # Convert OmegaConf types to native Python types and ensure strings
    if not OmegaConf.is_list(output_languages) and not isinstance(output_languages, list):
        raise ValueError("output_languages must be a list of language codes.")

    return [str(lang) for lang in output_languages]


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
def section_types_config(config: DictConfig, default_render_strategy_config: RenderStrategyName) -> dict[SectionTypeName, SectionType]:
    types = dict[SectionTypeName, SectionType]()
    for name, section_type in config["section_types"].items():
        params = dict(section_type)
        params["name"] = name
        # Use default_render_strategy if not specified in section_type
        if "render_strategy" not in params:
            params["render_strategy"] = default_render_strategy_config
        types[name] = SectionType.model_validate(params)
    return types


@cache(behavior="recompute")
def text_types_config(config: DictConfig) -> dict[TextTypeName, TextType]:
    types = dict[TextTypeName, TextType]()
    for name, text_type in config["text_types"].items():
        params = dict(text_type)
        params["name"] = name
        types[name] = TextType.model_validate(params)
    return types


@cache(behavior="recompute")
def text_group_types_config(config: DictConfig) -> dict[TextGroupTypeName, TextGroupType]:
    types = dict[TextGroupTypeName, TextGroupType]()
    for name, text_group_type in config["text_group_types"].items():
        params = dict(text_group_type)
        params["name"] = name
        types[name] = TextGroupType.model_validate(params)
    return types


@cache(behavior="recompute")
def default_render_strategy_config(config: DictConfig) -> RenderStrategyName:
    return RenderStrategyName(config.get("default_render_strategy", "html"))


@cache(behavior="recompute")
def render_strategy_config(config: DictConfig, render_strategies_config: dict[RenderStrategyName, RenderStrategy]) -> RenderStrategyName:
    strategy = RenderStrategyName(config["render_strategy"])
    if strategy != "dynamic" and strategy not in render_strategies_config:
        raise ValueError(f"Unknown render strategy: {strategy}")
    return strategy


@cache(behavior="recompute")
def render_strategies_config(config: DictConfig) -> dict[RenderStrategyName, RenderStrategy]:
    strategies = dict[RenderStrategyName, RenderStrategy]()
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
def activity_answers_prompts_config__none(
    config: DictConfig,
) -> dict[str, PromptConfig]:
    """Return empty dict when activity answer generation is disabled."""
    return {}


@cache(behavior="recompute")
def speech_prompt_config(config: DictConfig) -> SpeechPromptConfig:
    # Merge root-level speech config with prompt config
    prompt_config = cast(dict[str, Any], OmegaConf.to_container(config["prompts"]["speech_generation"], resolve=True))
    root_speech_config = cast(dict[str, Any], OmegaConf.to_container(config["speech"], resolve=True))

    # Merge the two configs, with root config providing provider settings
    merged_config = {**prompt_config, **root_speech_config}

    return SpeechPromptConfig.model_validate(merged_config)


@cache(behavior="recompute")
def voice_maps_config(speech_prompt_config: SpeechPromptConfig) -> dict[str, dict[str, str]]:
    """Load voice configuration maps from voices.yaml.

    This Hamilton node caches the voice maps once during pipeline execution,
    avoiding repeated file I/O and parsing on every TTS call.

    Returns:
        Dictionary mapping provider names to their voice configurations.
        Example: {"openai": {"en": "alloy", "default": "alloy"}, "azure": {...}}
    """
    with open(speech_prompt_config.voices_path, "r", encoding="utf-8") as f:
        voice_config = yaml.safe_load(f)
        return cast(dict[str, dict[str, str]], voice_config)


@cache(behavior="recompute")
def speech_instructions_config(
    speech_prompt_config: SpeechPromptConfig,
) -> dict[str, str]:
    """Load speech accent/pronunciation instructions from YAML.

    Returns:
        Dictionary mapping locale codes to instruction strings.
        Example: {"en-tz": "Speak in a Tanzanian English accent...", ...}
    """
    with open(speech_prompt_config.instructions_path, "r", encoding="utf-8") as f:
        return cast(dict[str, str], yaml.safe_load(f))


@cache(behavior="recompute")
def web_generation_html_prompt_config(config: DictConfig) -> HTMLPromptConfig:
    return HTMLPromptConfig.model_validate(prompt_config_with_model(config["prompts"]["web_generation_html"], config["default_model"]))


@cache(behavior="recompute")
def web_generation_activity_prompt_config(config: DictConfig) -> HTMLPromptConfig:
    return HTMLPromptConfig.model_validate(prompt_config_with_model(config["prompts"]["web_generation_activity"], config["default_model"]))


@cache(behavior="recompute")
def web_edit_prompt_config(config: DictConfig) -> HTMLPromptConfig:
    return HTMLPromptConfig.model_validate(prompt_config_with_model(config["prompts"]["web_edit"], config["default_model"]))


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
            "quiz_strategy": config["quiz_strategy"],
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


def pruned_text_types_config(config: DictConfig) -> list[TextTypeName]:
    return list[TextTypeName](config.get("text_filters", {}).get("pruned_text_types", []))


def pruned_section_types_config(config: DictConfig) -> list[SectionTypeName]:
    return list[SectionTypeName](config.get("section_filters", {}).get("pruned_section_types", []))


def quiz_count_section_types_config(config: DictConfig) -> list[SectionTypeName]:
    return list[SectionTypeName](config.get("section_filters", {}).get("quiz_count_section_types", []))


@cache(behavior="recompute")
def activity_strategy_config(config: DictConfig) -> str:
    """Get the activity generation strategy from config."""
    return str(config.get("activity_strategy", "none"))


@cache(behavior="recompute")
def styleguide_config(config: DictConfig) -> str:
    """Load the styleguide content from the configured styleguide file."""
    styleguide_path = str(config.get("styleguide", ""))
    if not styleguide_path:
        raise ValueError("No styleguide path configured. Set 'styleguide' in config (e.g., 'assets/styleguides/default.md').")

    if not os.path.exists(styleguide_path):
        raise FileNotFoundError(f"Styleguide file not found: {styleguide_path}")

    with open(styleguide_path, "r", encoding="utf-8") as f:
        content = f.read()

    log.info("loaded_styleguide", path=styleguide_path, length=len(content))
    return content


def active_section_types_config(
    section_types_config: dict[SectionTypeName, SectionType],
    render_strategies_config: dict[RenderStrategyName, RenderStrategy],
    activity_strategy_config: str,
) -> dict[SectionTypeName, SectionType]:
    """Filter out section types with activity render strategy when activity_strategy is none.

    This prevents configuration errors where sections are classified as activities
    but activity generation is disabled.
    """
    # Build set of active render strategies
    active_render_strategies = {
        name
        for name, strategy in render_strategies_config.items()
        if activity_strategy_config == "llm" or strategy.render_type != RenderType.activity
    }

    # Filter section types to only those using active render strategies
    return {
        section_name: section_type
        for section_name, section_type in section_types_config.items()
        if section_type.render_strategy in active_render_strategies
    }
