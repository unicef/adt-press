from hamilton.function_modifiers import cache
from omegaconf import DictConfig, OmegaConf

from adt_press.models.config import TemplateConfig
from adt_press.models.image import ProcessedImage, PrunedImage
from adt_press.models.pdf import Page
from adt_press.models.plate import Plate
from adt_press.models.section import PageSections, SectionExplanation, SectionGlossary
from adt_press.models.speech import SpeechFile
from adt_press.models.text import EasyReadText, OutputText, PageText, PageTexts
from adt_press.models.web import WebPage
from adt_press.utils.html import render_template
from adt_press.utils.languages import LANGUAGE_MAP


@cache(behavior="recompute")
def report_processed_images(template_config: TemplateConfig, processed_images: list[ProcessedImage]) -> str:
    return render_template(template_config, "templates/processed_images.html", dict(images=processed_images))


@cache(behavior="recompute")
def report_pruned_images(template_config: TemplateConfig, pruned_images: list[PrunedImage]) -> str:
    return render_template(template_config, "templates/pruned_images.html", dict(images=pruned_images))


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
    easy_reads_by_text_id: dict[str, EasyReadText],
    input_language_config: str,
    plate_language_config: str,
) -> str:
    input_language = LANGUAGE_MAP[input_language_config]
    output_language = LANGUAGE_MAP[plate_language_config]

    return render_template(
        template_config,
        "templates/page_report.html",
        dict(
            pages=pdf_pages,
            texts=filtered_pdf_texts,
            sections=filtered_sections_by_page_id,
            texts_by_id=filtered_pdf_texts_by_id,
            images_by_id=processed_images_by_id,
            explanations=explanations_by_section_id,
            output_texts=output_pdf_texts_by_id,
            section_glossaries=section_glossaries_by_id,
            easy_reads=easy_reads_by_text_id,
            input_language=input_language,
            output_language=output_language,
        ),
    )


@cache(behavior="recompute")
def plate_report(template_config: TemplateConfig, plate: Plate) -> str:
    texts_by_id = {t.text_id: t for t in plate.texts}
    images_by_id = {i.image_id: i for i in plate.images}

    return render_template(
        template_config, "templates/plate_report.html", dict(plate=plate, texts_by_id=texts_by_id, images_by_id=images_by_id)
    )


@cache(behavior="recompute")
def report_config(template_config: TemplateConfig, config: DictConfig) -> str:
    return render_template(template_config, "templates/config.html", dict(config=OmegaConf.to_yaml(config)))


@cache(behavior="recompute")
def translation_report(
    template_config: TemplateConfig,
    output_languages_config: list[str],
    plate: Plate,
    plate_translations: dict[str, dict[str, str]],
    speech_files: dict[str, dict[str, SpeechFile]],
) -> str:
    return render_template(
        template_config,
        "templates/translation_report.html",
        dict(
            plate=plate,
            output_languages=output_languages_config,
            translations=plate_translations,
            speech_files=speech_files,
            LANGUAGE_MAP=LANGUAGE_MAP,
        ),
    )


@cache(behavior="recompute")
def web_report(
    template_config: TemplateConfig,
    web_pages: list[WebPage],
) -> str:
    return render_template(
        template_config,
        "templates/web_report.html",
        dict(
            web_pages=web_pages,
        ),
    )


@cache(behavior="recompute")
def report_index(
    template_config: TemplateConfig,
    report_processed_images: str,
    report_pruned_images: str,
    report_pages: str,
    report_config: str,
    package_adt_web: str,
    plate_report: str,
    web_report: str,
    translation_report: str,
) -> str:
    return render_template(
        template_config,
        "templates/index.html",
        dict(
            report_processed_images=report_processed_images,
            report_pruned_images=report_pruned_images,
            report_pages=report_pages,
            report_config=report_config,
            package_adt_web=package_adt_web,
        ),
    )
