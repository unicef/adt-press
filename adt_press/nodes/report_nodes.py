from hamilton.function_modifiers import cache
from omegaconf import DictConfig, OmegaConf

from adt_press.nodes.config_nodes import TemplateConfig
from adt_press.utils.image import ProcessedImage
from adt_press.utils.pdf import Page
from adt_press.utils.web import render_template


@cache(behavior="recompute")
def report_images(template_config: TemplateConfig, pdf_processed_images: list[ProcessedImage]) -> str:
    return render_template(template_config, "image_report.html", dict(images=pdf_processed_images))


@cache(behavior="recompute")
def report_pages(template_config: TemplateConfig, pdf_pages: list[Page]) -> str:
    return render_template(template_config, "page_report.html", dict(pages=pdf_pages))


@cache(behavior="recompute")
def report_config(template_config: TemplateConfig, config: DictConfig) -> str:
    return render_template(template_config, "config.html", dict(config=OmegaConf.to_yaml(config)))


@cache(behavior="recompute")
def report_index(template_config: TemplateConfig, report_images: str, report_pages: str, report_config: str) -> str:
    return render_template(template_config, "index.html", dict())
