from adt_press.llm.prompt import PromptConfig
from adt_press.llm.text_extraction import get_page_text
from adt_press.nodes.config_nodes import PageRangeConfig
from adt_press.utils.image import Image
from adt_press.utils.pdf import Page, PageText, pages_for_pdf
from adt_press.utils.sync import gather_with_limit, run_async_task


def pdf_images(pdf_pages: list[Page]) -> list[Image]:
    pdf_images = []
    for page in pdf_pages:
        pdf_images.extend(page.images)
    return pdf_images


def pdf_text(pdf_pages: list[Page], text_extraction_prompt_config: PromptConfig) -> list[PageText]:
    async def extract_text():
        text = []
        for page in pdf_pages:
            text.append(get_page_text(text_extraction_prompt_config, page))

        return await gather_with_limit(text, text_extraction_prompt_config.rate_limit)

    return run_async_task(extract_text)


def pdf_pages(output_dir_config: str, pdf_path_config: str, pdf_hash_config: str, page_range_config: PageRangeConfig) -> list[Page]:
    return pages_for_pdf(output_dir_config, pdf_path_config, page_range_config.start, page_range_config.end)
