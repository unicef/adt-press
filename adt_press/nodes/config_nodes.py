import os

from hamilton.function_modifiers import cache
from omegaconf import DictConfig
from pydantic import BaseModel

from adt_press.llm.image_crop import CropPromptConfig
from adt_press.models.config import HTMLPromptConfig, PageRangeConfig, PromptConfig, RowPromptConfig
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
def page_sectioning_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(prompt_config_with_model(config["prompts"]["page_sectioning"], config["default_model"]))


@cache(behavior="recompute")
def section_explanation_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(prompt_config_with_model(config["prompts"]["section_explanation"], config["default_model"]))


@cache(behavior="recompute")
def text_translation_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(prompt_config_with_model(config["prompts"]["text_translation"], config["default_model"]))


@cache(behavior="recompute")
def section_glossary_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(prompt_config_with_model(config["prompts"]["section_glossary"], config["default_model"]))


@cache(behavior="recompute")
def section_easy_read_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(prompt_config_with_model(config["prompts"]["section_easy_read"], config["default_model"]))


@cache(behavior="recompute")
def speech_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(prompt_config_with_model(config["prompts"]["speech_generation"], config["default_model"]))


@cache(behavior="recompute")
def web_generation_html_prompt_config(config: DictConfig) -> HTMLPromptConfig:
    return HTMLPromptConfig.model_validate(prompt_config_with_model(config["prompts"]["web_generation_html"], config["default_model"]))


@cache(behavior="recompute")
def web_generation_rows_prompt_config(config: DictConfig) -> RowPromptConfig:
    return RowPromptConfig.model_validate(prompt_config_with_model(config["prompts"]["web_generation_rows"], config["default_model"]))


def image_config(config: DictConfig) -> DictConfig:
    return DictConfig(config.get("image_filters", {}))


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
