from hamilton.function_modifiers import cache
from omegaconf import DictConfig, OmegaConf

from adt_press.models.config import MetadataPromptConfig, TemplateConfig
from adt_press.models.image import ProcessedImage, PrunedImage
from adt_press.models.metadata import BookMetadata
from adt_press.models.pdf import Page
from adt_press.models.plate import Plate, PlateSection
from adt_press.models.section import GlossaryItem, PageSections, SectionExplanation, SectionGlossary, SectionQuiz
from adt_press.models.speech import SpeechFile
from adt_press.models.text import EasyReadText, OutputText, PageText, PageTextGroup, PageTexts
from adt_press.models.web import WebPage
from adt_press.utils.html import render_template
from adt_press.utils.languages import LANGUAGE_MAP
from adt_press.utils.report_assets import compile_tailwind_for_reports


@cache(behavior="recompute")
def report_processed_images(template_config: TemplateConfig, processed_images: list[ProcessedImage]) -> str:
    return render_template(template_config, "templates/processed_images.html", dict(images=processed_images))


@cache(behavior="recompute")
def report_pruned_images(template_config: TemplateConfig, pruned_images: list[PrunedImage]) -> str:
    return render_template(template_config, "templates/pruned_images.html", dict(images=pruned_images))


@cache(behavior="recompute")
def report_quizzes(
    template_config: TemplateConfig,
    pdf_pages: list[Page],
    sections_by_page_id: dict[str, PageSections],
    quizzes_by_section_id: dict[str, SectionQuiz],
) -> str:
    return render_template(
        template_config,
        "templates/quiz_report.html",
        dict(
            pages=pdf_pages,
            quizzes=quizzes_by_section_id,
            sections=sections_by_page_id,
        ),
    )


@cache(behavior="recompute")
def report_pages(
    template_config: TemplateConfig,
    pdf_pages: list[Page],
    processed_pdf_texts: dict[str, PageTexts],
    filtered_sections_by_page_id: dict[str, PageSections],
    processed_pdf_texts_by_id: dict[str, PageText],
    pdf_text_groups_by_id: dict[str, PageTextGroup],
    processed_images_by_id: dict[str, ProcessedImage],
    explanations_by_section_id: dict[str, SectionExplanation],
    plate_output_texts_by_id: dict[str, OutputText],
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
            texts=processed_pdf_texts,
            sections=filtered_sections_by_page_id,
            texts_by_id=processed_pdf_texts_by_id,
            images_by_id=processed_images_by_id,
            groups_by_id=pdf_text_groups_by_id,
            explanations=explanations_by_section_id,
            output_texts=plate_output_texts_by_id,
            section_glossaries=section_glossaries_by_id,
            easy_reads=easy_reads_by_text_id,
            input_language=input_language,
            output_language=output_language,
        ),
    )


@cache(behavior="recompute")
def plate_report(template_config: TemplateConfig, plate: Plate, strategy_config: dict[str, str]) -> str:
    texts_by_id = {t.text_id: t for t in plate.texts}
    images_by_id = {i.image_id: i for i in plate.images}
    groups_by_id = {g.group_id: g for g in plate.groups}
    quizzes_by_section_id = {q.section_id: q for q in plate.quizzes}

    return render_template(
        template_config,
        "templates/plate_report.html",
        dict(
            plate=plate,
            texts_by_id=texts_by_id,
            images_by_id=images_by_id,
            groups_by_id=groups_by_id,
            quizzes_by_section_id=quizzes_by_section_id,
            strategy_config=strategy_config,
        ),
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
def glossary_report(
    template_config: TemplateConfig,
    plate: Plate,
    output_languages_config: list[str],
    plate_glossary_translations: dict[str, list[GlossaryItem]],
) -> str:
    return render_template(
        template_config,
        "templates/glossary_report.html",
        dict(
            plate=plate,
            output_languages=output_languages_config,
            glossary_translations=plate_glossary_translations,
            LANGUAGE_MAP=LANGUAGE_MAP,
        ),
    )


@cache(behavior="recompute")
def metadata_report(
    template_config: TemplateConfig,
    book_metadata: BookMetadata,
    pdf_pages: list[Page],
    pdf_pages_by_id: dict[str, Page],
    metadata_extraction_prompt_config: MetadataPromptConfig,
) -> str:
    # Find the cover page if specified
    cover_page = None
    if book_metadata.cover_page_id:
        cover_page = pdf_pages_by_id.get(book_metadata.cover_page_id)

    # Get the pages used for metadata extraction (first N pages)
    page_range = metadata_extraction_prompt_config.page_range
    pages_used_for_metadata = pdf_pages[:page_range] if page_range > 0 else []

    return render_template(
        template_config,
        "templates/metadata_report.html",
        dict(
            metadata=book_metadata,
            cover_page=cover_page,
            pages_analyzed=metadata_extraction_prompt_config.page_range,
            pages_used=pages_used_for_metadata,
        ),
    )


@cache(behavior="recompute")
def web_report(
    template_config: TemplateConfig,
    web_pages: list[WebPage],
    plate: Plate,
    plate_sections_by_id: dict[str, PlateSection],
) -> str:
    sections_lookup = dict(plate_sections_by_id)
    for quiz in plate.quizzes:
        parent_section = plate_sections_by_id.get(quiz.section_id)
        if parent_section and quiz.quiz_id not in sections_lookup:
            sections_lookup[quiz.quiz_id] = parent_section

    return render_template(
        template_config,
        "templates/web_report.html",
        dict(
            web_pages=web_pages,
            sections=sections_lookup,
        ),
    )


@cache(behavior="recompute")
def report_index(
    template_config: TemplateConfig,
    run_output_dir_config: str,
    report_processed_images: str,
    report_pruned_images: str,
    report_pages: str,
    report_config: str,
    package_adt_web: str,
    plate_report: str,
    web_report: str,
    translation_report: str,
    metadata_report: str,
) -> str:
    index_html = render_template(
        template_config,
        "templates/index.html",
        dict(
            report_processed_images=report_processed_images,
            report_pruned_images=report_pruned_images,
            report_pages=report_pages,
            report_config=report_config,
            package_adt_web=package_adt_web,
            metadata_report=metadata_report,
        ),
    )

    # Compile Tailwind CSS for all report files
    report_files = [
        report_processed_images,
        report_pruned_images,
        report_pages,
        report_config,
        plate_report,
        web_report,
        translation_report,
        metadata_report,
        index_html,
    ]

    try:
        compile_tailwind_for_reports(
            output_dir=run_output_dir_config,
            report_files=report_files,
        )
    except Exception as e:
        import structlog

        logger = structlog.get_logger()
        logger.error(
            "Failed to compile Tailwind CSS for reports",
            error=str(e),
        )

    return index_html
