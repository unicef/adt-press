from hamilton.function_modifiers import cache
from pydantic import BaseModel

from adt_press.llm.prompt import PromptConfig
from adt_press.utils.file import calculate_file_hash
from adt_press.utils.web import TemplateConfig

from omegaconf import OmegaConf

def config() -> OmegaConf:
    return OmegaConf.create({})


def template_config(output_dir_config: str, template_dir_config: str) -> TemplateConfig:
    return TemplateConfig(output_dir=output_dir_config, template_dir=template_dir_config)


def pdf_path_config(config: OmegaConf) -> str:
    return config["pdf_path"]


def output_language_config(config: OmegaConf) -> str:
    return config.get("output_language", "en")


def output_dir_config(config: OmegaConf) -> str:
    return config["output_dir"]


def template_dir_config(config: OmegaConf) -> str:
    return config["template_dir"]


@cache(behavior="recompute")
def pdf_hash_config(pdf_path_config: str) -> str:
    return calculate_file_hash(pdf_path_config)


class PageRangeConfig(BaseModel):
    start: int = 0
    end: int = 0


def page_range_config(config: OmegaConf) -> PageRangeConfig:
    return PageRangeConfig.model_validate(config.get("page_range", {}))


@cache(behavior="recompute")
def caption_prompt_config(config: OmegaConf) -> PromptConfig:
    return PromptConfig.model_validate(config["prompts"]["caption"])


@cache(behavior="recompute")
def crop_prompt_config(config: OmegaConf) -> PromptConfig:
    return PromptConfig.model_validate(config["prompts"]["crop"])


@cache(behavior="recompute")
def meaningfulness_prompt_config(config: OmegaConf) -> PromptConfig:
    return PromptConfig.model_validate(config["prompts"]["meaningfulness"])


def image_config(config: OmegaConf) -> dict:
    return config.get("image_filters", {})


class ImageSizeFilterConfig(BaseModel):
    max_side: int = 500
    min_side: int = 50


def image_size_filter_config(image_config: dict) -> ImageSizeFilterConfig:
    return ImageSizeFilterConfig.model_validate(image_config.get("size", {}))


class BlankImageFilterConfig(BaseModel):
    threshold: int = 2


def blank_image_filter_config(image_config: dict) -> BlankImageFilterConfig:
    return BlankImageFilterConfig.model_validate(image_config.get("blank", {}))
