import json
import os

from hamilton.function_modifiers import config

from adt_press.llm.metadata_extraction import get_metadata
from adt_press.llm.text_easy_read import get_text_easy_read
from adt_press.llm.text_extraction import get_page_text
from adt_press.models.config import MetadataPromptConfig, PromptConfig, TextGroupType, TextType
from adt_press.models.image import Image
from adt_press.models.metadata import BookChapter, BookMetadata
from adt_press.models.pdf import Page
from adt_press.models.text import EasyReadText, PageText, PageTextGroup, PageTexts
from adt_press.nodes.config_nodes import PageRangeConfig
from adt_press.utils.file import copy_file
from adt_press.utils.languages import Language
from adt_press.utils.pdf import extract_pdf_to_dir
from adt_press.utils.sync import gather_with_limit, run_async_task


def pdf_pages_by_id(pdf_pages: list[Page]) -> dict[str, Page]:
    return {p.page_id: p for p in pdf_pages}


def pdf_images(pdf_pages: list[Page]) -> list[Image]:
    pdf_images = []
    for page in pdf_pages:
        pdf_images.extend(page.images)
    return pdf_images


def pdf_texts(
    run_output_dir_config: str,
    pdf_pages: list[Page],
    text_extraction_prompt_config: PromptConfig,
    text_types_config: dict[str, TextType],
    text_group_types_config: dict[str, TextGroupType],
    input_language: Language,
) -> dict[str, PageTexts]:
    async def extract_text():
        text = []
        for page in pdf_pages:
            text.append(
                get_page_text(
                    run_output_dir_config,
                    f"page_{page.page_id}",
                    text_extraction_prompt_config,
                    text_types_config,
                    text_group_types_config,
                    page,
                    input_language,
                )
            )

        return await gather_with_limit(text, text_extraction_prompt_config.rate_limit)

    texts = {pt.page_id: pt for pt in run_async_task(extract_text)}
    return texts


@config.when(easy_read_strategy="llm")
def easy_reads_by_text_id__llm(
    input_language: Language,
    text_easy_read_prompt_config: PromptConfig,
    processed_pdf_texts: dict[str, PageTexts],
) -> dict[str, EasyReadText]:
    async def get_easy_reads():
        tasks = []
        for page_texts in processed_pdf_texts.values():
            for group in page_texts.groups:
                for text in group.texts:
                    tasks.append(get_text_easy_read(input_language, text_easy_read_prompt_config, text))

        return await gather_with_limit(tasks, text_easy_read_prompt_config.rate_limit)

    results = run_async_task(get_easy_reads)
    return {easy_read.text_id: easy_read for easy_read in results}


@config.when(easy_read_strategy="none")
def easy_reads_by_text_id__none(
    input_language: Language,
    text_easy_read_prompt_config: PromptConfig,
    processed_pdf_texts: dict[str, PageTexts],
) -> dict[str, EasyReadText]:
    return {}


def processed_pdf_texts(pruned_text_types_config: list[str], pdf_texts: dict[str, PageTexts]) -> dict[str, PageTexts]:
    filtered_texts = {}
    for page_id, page_texts in pdf_texts.items():
        groups = []
        for g in page_texts.groups:
            group_texts = [
                PageText(
                    text_id=t.text_id,
                    text=t.text,
                    text_type=t.text_type,
                    is_pruned=t.text_type in pruned_text_types_config,
                )
                for t in g.texts
            ]

            groups.append(PageTextGroup(group_id=g.group_id, group_type=g.group_type, texts=group_texts))

        filtered_texts[page_id] = PageTexts(
            page_id=page_id,
            groups=groups,
            reasoning=page_texts.reasoning,
        )

    return filtered_texts


def filtered_pdf_texts(processed_pdf_texts: dict[str, PageTexts]) -> dict[str, PageTexts]:
    unpruned_texts = {}
    for page_id, page_texts in processed_pdf_texts.items():
        groups = []
        for g in page_texts.groups:
            group_texts = [t for t in g.texts if not t.is_pruned]
            if group_texts:
                groups.append(PageTextGroup(group_id=g.group_id, group_type=g.group_type, texts=group_texts))

        unpruned_texts[page_id] = PageTexts(
            page_id=page_id,
            groups=groups,
            reasoning=page_texts.reasoning,
        )

    return unpruned_texts


def processed_pdf_texts_by_id(processed_pdf_texts: dict[str, PageTexts]) -> dict[str, PageText]:
    texts = {}
    for pt in processed_pdf_texts.values():
        for g in pt.groups:
            for t in g.texts:
                texts[t.text_id] = t
    return texts


def pdf_text_groups_by_id(processed_pdf_texts: dict[str, PageTexts]) -> dict[str, PageTextGroup]:
    groups = {}
    for pt in processed_pdf_texts.values():
        for g in pt.groups:
            groups[g.group_id] = g
    return groups


def pdf_extraction_dir(
    run_output_dir_config: str, pdf_path_config: str, page_range_config: PageRangeConfig, page_grouping_config: str
) -> str:
    """
    Extract PDF metadata and content to extraction directory.

    Returns:
        Path to the extraction directory containing pdf_extract.json
    """
    spread_mode = page_grouping_config == "spread"
    return extract_pdf_to_dir(run_output_dir_config, pdf_path_config, page_range_config.start, page_range_config.end, spread_mode)


def pdf_pages(run_output_dir_config: str, pdf_extraction_dir: str) -> list[Page]:
    """
    Read extracted pages from the extraction directory.

    Args:
        run_output_dir_config: Output directory containing images subdirectory
        pdf_extraction_dir: Directory containing pdf_extract.json from extraction

    Returns:
        List of Page objects with extracted content
    """
    # Create images directory for copying images
    images_dir = os.path.join(run_output_dir_config, "images")
    os.makedirs(images_dir, exist_ok=True)

    # Parse the results
    results_file = os.path.join(pdf_extraction_dir, "pdf_extract.json")
    if not os.path.exists(results_file):
        raise RuntimeError(f"Extraction results file not found: {results_file}")

    with open(results_file, "r") as f:
        extract_data = json.load(f)

    # Convert to our models and copy images to images directory
    pages = []
    for page_data in extract_data["pages"]:
        # Convert images and copy them to images directory
        images = []
        for img_data in page_data["images"]:
            image = Image(
                image_id=img_data["image_id"],
                page_id=img_data["page_id"],
                index=img_data["index"],
                image_path=copy_file(pdf_extraction_dir, images_dir, img_data["image_path"]),
                chart_path=copy_file(pdf_extraction_dir, images_dir, img_data["chart_path"]),
                width=img_data["width"],
                height=img_data["height"],
                image_type=img_data["image_type"],
            )
            images.append(image)

        # Create page object with copied image path
        page = Page(
            page_id=page_data["page_id"],
            page_number=page_data["page_number"],
            page_image_path=copy_file(pdf_extraction_dir, images_dir, page_data["page_image_path"]),
            text=page_data["text"],
            images=images,
        )
        pages.append(page)

    return pages


def pdf_metadata(pdf_extraction_dir: str) -> dict[str, object]:
    """
    Extract PDF metadata from the extraction directory.

    Args:
        pdf_extraction_dir: Directory containing pdf_extract.json from extraction

    Returns:
        Dictionary of PDF metadata extracted from the PDF file's Info dictionary
    """
    results_file = os.path.join(pdf_extraction_dir, "pdf_extract.json")
    if not os.path.exists(results_file):
        raise RuntimeError(f"Extraction results file not found: {results_file}")

    with open(results_file, "r") as f:
        extract_data = json.load(f)

    return dict[str, object](extract_data.get("pdf_metadata", {}))


def book_metadata(
    pdf_pages: list[Page],
    pdf_metadata: dict[str, object],
    metadata_extraction_prompt_config: MetadataPromptConfig,
) -> BookMetadata:
    """
    Extract book metadata (title, author, cover page) from the first pages.

    Args:
        pdf_pages: All extracted pages from the PDF
        pdf_metadata: PDF metadata from the PDF file's Info dictionary
        metadata_extraction_prompt_config: Configuration for the LLM prompt including page_range

    Returns:
        Metadata object with extracted title, author, and cover page identification
    """
    # Get the first N pages for analysis
    pages_to_analyze = pdf_pages[: metadata_extraction_prompt_config.page_range]

    async def extract_metadata() -> BookMetadata:
        return await get_metadata(metadata_extraction_prompt_config, pages_to_analyze, pdf_metadata)

    return run_async_task(extract_metadata)


def book_table_of_contents(book_metadata: BookMetadata) -> list[BookChapter]:
    return book_metadata.table_of_contents


def input_language(input_language_config: str, book_metadata: BookMetadata) -> Language:
    if input_language_config != "auto":
        return Language.from_code(input_language_config)
    if book_metadata.language_code:
        return Language.from_code(book_metadata.language_code)
    raise ValueError("Input language could not be determined from config or book metadata, please specify input_language in config.")


def plate_language(plate_language_config: str, input_language: Language) -> Language:
    if plate_language_config == "auto":
        return input_language
    return Language.from_code(plate_language_config)


def output_languages(output_languages_config: list[str], plate_language: Language) -> list[Language]:
    # Handle special case of exactly ["auto"]
    if output_languages_config == ["auto"]:
        return [plate_language]

    # Process each language code, replacing "auto" with plate_language
    result = []
    for lang_code in output_languages_config:
        # Replace "auto" or unresolved interpolations with plate_language
        if lang_code in ("auto", "${plate_language}", "${input_language}"):
            if plate_language not in result:  # Avoid duplicates
                result.append(plate_language)
        else:
            lang = Language.from_code(lang_code)
            if lang not in result:  # Avoid duplicates
                result.append(lang)

    return result if result else [plate_language]
