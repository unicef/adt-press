from hamilton.function_modifiers import cache
from omegaconf import DictConfig
from pydantic import BaseModel

from adt_press.llm.image_crop import CropPromptConfig
from adt_press.models.config import PageRangeConfig, PromptConfig
from adt_press.utils.config import conf_to_object
from adt_press.utils.file import calculate_file_hash
from adt_press.utils.html import TemplateConfig


def config() -> DictConfig:  # pragma: no cover
    assert False, "This function should not be called directly. Use the config from the pipeline instead."


def template_config(output_dir_config: str, template_dir_config: str) -> TemplateConfig:
    return TemplateConfig(output_dir=output_dir_config, template_dir=template_dir_config)


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


def output_dir_config(config: DictConfig) -> str:
    return str(config["output_dir"])


def template_dir_config(config: DictConfig) -> str:
    return str(config["template_dir"])


def pdf_title_config(config: DictConfig) -> str:
    return str(config["pdf_title"])


@cache(behavior="recompute")
def pdf_hash_config(pdf_path_config: str) -> str:
    return calculate_file_hash(pdf_path_config)


def page_range_config(config: DictConfig) -> PageRangeConfig:
    return PageRangeConfig.model_validate(config.get("page_range", {}))


@cache(behavior="recompute")
def caption_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(conf_to_object(config["prompts"]["caption"]))


@cache(behavior="recompute")
def crop_prompt_config(config: DictConfig) -> CropPromptConfig:
    return CropPromptConfig.model_validate(conf_to_object(config["prompts"]["crop"]))


@cache(behavior="recompute")
def meaningfulness_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(conf_to_object(config["prompts"]["meaningfulness"]))


@cache(behavior="recompute")
def text_extraction_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(conf_to_object(config["prompts"]["text_extraction"]))


@cache(behavior="recompute")
def page_sectioning_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(conf_to_object(config["prompts"]["page_sectioning"]))


@cache(behavior="recompute")
def section_explanation_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(conf_to_object(config["prompts"]["section_explanation"]))


@cache(behavior="recompute")
def text_translation_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(conf_to_object(config["prompts"]["text_translation"]))


@cache(behavior="recompute")
def section_glossary_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(conf_to_object(config["prompts"]["section_glossary"]))


@cache(behavior="recompute")
def section_easy_read_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(conf_to_object(config["prompts"]["section_easy_read"]))


@cache(behavior="recompute")
def web_generation_prompt_config(config: DictConfig) -> PromptConfig:
    return PromptConfig.model_validate(conf_to_object(config["prompts"]["web_generation"]))


@cache(behavior="recompute")
def web_generation_examples_config(config: DictConfig) -> list[str]:
    return list[str](config.get("web_generation_examples", []))


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
