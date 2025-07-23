from hamilton.function_modifiers import cache
from omegaconf import DictConfig, OmegaConf

from adt_press.nodes.config_nodes import TemplateConfig
from adt_press.utils.image import ProcessedImage, PrunedImage
from adt_press.utils.pdf import Page
from adt_press.utils.web import render_template


@cache(behavior="recompute")
def report_processed_images(template_config: TemplateConfig, processed_images: list[ProcessedImage]) -> str:
    return render_template(template_config, "processed_images.html", dict(images=processed_images))


@cache(behavior="recompute")
def report_pruned_images(template_config: TemplateConfig, pruned_images: list[PrunedImage]) -> str:
    return render_template(template_config, "pruned_images.html", dict(images=pruned_images))


@cache(behavior="recompute")
def report_pages(template_config: TemplateConfig, pdf_pages: list[Page]) -> str:
    return render_template(template_config, "page_report.html", dict(pages=pdf_pages))


@cache(behavior="recompute")
def report_config(template_config: TemplateConfig, config: DictConfig) -> str:
    return render_template(template_config, "config.html", dict(config=OmegaConf.to_yaml(config)))


@cache(behavior="recompute")
def report_index(
    template_config: TemplateConfig, report_processed_images: str, report_pruned_images: str, report_pages: str, report_config: str
) -> str:
    return render_template(template_config, "index.html", dict())
