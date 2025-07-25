from adt_press.llm.page_sectioning import get_page_sections
from adt_press.llm.prompt import PromptConfig
from adt_press.llm.text_extraction import get_page_text
from adt_press.nodes.config_nodes import PageRangeConfig
from adt_press.utils.image import Image, ProcessedImage
from adt_press.utils.pdf import Page, PageSections, PageText, PageTexts, pages_for_pdf
from adt_press.utils.sync import gather_with_limit, run_async_task


def pdf_images(pdf_pages: list[Page]) -> list[Image]:
    pdf_images = []
    for page in pdf_pages:
        pdf_images.extend(page.images)
    return pdf_images


def pdf_texts(pdf_pages: list[Page], text_extraction_prompt_config: PromptConfig) -> dict[str, PageTexts]:
    async def extract_text():
        text = []
        for page in pdf_pages:
            text.append(get_page_text(text_extraction_prompt_config, page))

        return await gather_with_limit(text, text_extraction_prompt_config.rate_limit)

    return {p.page_id: p for p in run_async_task(extract_text)}

def pdf_texts_by_id(pdf_texts: dict[str, PageTexts]) -> dict[str, PageText]:
    return {t.text_id: t for page_texts in pdf_texts.values() for t in page_texts.text}

def pdf_sections(pdf_pages: list[Page], processed_images_by_page: dict[str, list[ProcessedImage]], pdf_texts: dict[str, PageTexts], page_sectioning_prompt_config: PromptConfig) -> dict[str, PageSections]:
    page_sections = {}

    async def section_pages():
        sections = []
        for page in pdf_pages:
            page_images = processed_images_by_page[page.page_id]
            page_texts = pdf_texts[page.page_id]

            # if we didn't extract any good images or text, we skip sectioning this page
            if not page_images and not page_texts.text:
                page_sections[page.page_id] = PageSections(page_id=page.page_id, sections=[], reasoning="No images or text to section")
            else:
                sections.append(get_page_sections(page_sectioning_prompt_config, page, page_images, page_texts))

        return await gather_with_limit(sections, page_sectioning_prompt_config.rate_limit)

    sections = run_async_task(section_pages)
    for p in sections:
        page_sections[p.page_id] = p
    return page_sections

def pdf_pages(output_dir_config: str, pdf_path_config: str, pdf_hash_config: str, page_range_config: PageRangeConfig) -> list[Page]:
    return pages_for_pdf(output_dir_config, pdf_path_config, page_range_config.start, page_range_config.end)
