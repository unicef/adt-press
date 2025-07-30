from hamilton.function_modifiers import cache
from omegaconf import DictConfig, OmegaConf

from adt_press.nodes.config_nodes import TemplateConfig
from adt_press.utils.image import ProcessedImage, PrunedImage
from adt_press.utils.languages import LANGUAGE_MAP
from adt_press.utils.pdf import OutputText, Page, PageSections, PageText, PageTexts, SectionEasyRead, SectionExplanation, SectionGlossary
from adt_press.utils.web import render_template


@cache(behavior="recompute")
def report_processed_images(template_config: TemplateConfig, processed_images: list[ProcessedImage]) -> str:
    return render_template(template_config, "processed_images.html", dict(images=processed_images))


@cache(behavior="recompute")
def report_pruned_images(template_config: TemplateConfig, pruned_images: list[PrunedImage]) -> str:
    return render_template(template_config, "pruned_images.html", dict(images=pruned_images))


@cache(behavior="recompute")
def report_pages(
    template_config: TemplateConfig,
    pdf_pages: list[Page],
    filtered_pdf_texts: dict[str, PageTexts],
    filtered_sections_by_page_id: dict[str, PageSections],
    filtered_pdf_texts_by_id: dict[str, PageText],
    processed_images_by_id: dict[str, ProcessedImage],
    explanations_by_section_id: dict[str, SectionExplanation],
    output_pdf_texts_by_id: dict[str, OutputText],
    section_glossaries_by_id: dict[str, SectionGlossary],
    section_easy_reads_by_id: dict[str, SectionEasyRead],
    input_language_config: str,
    output_language_config: str,
) -> str:
    input_language = LANGUAGE_MAP[input_language_config]
    output_language = LANGUAGE_MAP[output_language_config]

    return render_template(
        template_config,
        "page_report.html",
        dict(
            pages=pdf_pages,
            texts=filtered_pdf_texts,
            sections=filtered_sections_by_page_id,
            texts_by_id=filtered_pdf_texts_by_id,
            images_by_id=processed_images_by_id,
            explanations=explanations_by_section_id,
            output_texts=output_pdf_texts_by_id,
            section_glossaries=section_glossaries_by_id,
            section_easy_reads=section_easy_reads_by_id,
            input_language=input_language,
            output_language=output_language,
        ),
    )


@cache(behavior="recompute")
def report_config(template_config: TemplateConfig, config: DictConfig) -> str:
    return render_template(template_config, "config.html", dict(config=OmegaConf.to_yaml(config)))


@cache(behavior="recompute")
def report_index(
    template_config: TemplateConfig, report_processed_images: str, report_pruned_images: str, report_pages: str, report_config: str
) -> str:
    return render_template(template_config, "index.html", dict())
