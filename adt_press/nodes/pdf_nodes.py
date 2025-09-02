import os

from adt_press.llm.text_easy_read import get_text_easy_read
from adt_press.llm.text_extraction import get_page_text
from adt_press.llm.text_translation import get_text_translation
from adt_press.models.config import PromptConfig
from adt_press.models.image import Image
from adt_press.models.pdf import Page
from adt_press.models.text import EasyReadText, OutputText, PageText, PageTexts
from adt_press.nodes.config_nodes import PageRangeConfig
from adt_press.utils.pdf import pages_for_pdf
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


def easy_reads_by_text_id(
    input_language_config: str,
    text_easy_read_prompt_config: PromptConfig,
    filtered_pdf_texts: dict[str, PageTexts],
) -> dict[str, EasyReadText]:
    async def get_easy_reads():
        tasks = []
        for page_texts in filtered_pdf_texts.values():
            for text in page_texts.texts:
                tasks.append(get_text_easy_read(input_language_config, text_easy_read_prompt_config, text))

        return await gather_with_limit(tasks, text_easy_read_prompt_config.rate_limit)

    results = run_async_task(get_easy_reads)
    return {easy_read.text_id: easy_read for easy_read in results}


def filtered_pdf_texts(pruned_text_types_config: list[str], pdf_texts: dict[str, PageTexts]) -> dict[str, PageTexts]:
    filtered_texts = {}
    for page_id, page_texts in pdf_texts.items():
        filtered_texts[page_id] = PageTexts(
            page_id=page_id,
            reasoning=page_texts.reasoning,
            texts=[
                PageText(
                    text_id=t.text_id,
                    text=t.text,
                    text_type=t.text_type,
                    is_pruned=t.text_type in pruned_text_types_config,
                )
                for t in page_texts.texts
            ],
        )
    return filtered_texts


def filtered_pdf_texts_by_id(filtered_pdf_texts: dict[str, PageTexts]) -> dict[str, PageText]:
    return {t.text_id: t for page_texts in filtered_pdf_texts.values() for t in page_texts.texts}


def output_pdf_texts_by_id(
    text_translation_prompt_config: PromptConfig,
    filtered_pdf_texts: dict[str, PageTexts],
    easy_reads_by_text_id: dict[str, EasyReadText],
    input_language_config: str,
    plate_language_config: str,
) -> dict[str, OutputText]:
    texts_by_id = {}

    # noop if input and output languages are the same
    if input_language_config == plate_language_config:
        for page_texts in filtered_pdf_texts.values():
            for text in page_texts.texts:
                texts_by_id[text.text_id] = OutputText(
                    text_id=text.text_id,
                    text=text.text,
                    language_code=input_language_config,
                    reasoning="",
                )
                easy_read = easy_reads_by_text_id[text.text_id]
                texts_by_id[easy_read.easy_read_id] = OutputText(
                    text_id=easy_read.easy_read_id,
                    text=easy_read.easy_read,
                    language_code=input_language_config,
                    reasoning=easy_read.reasoning,
                )

        return texts_by_id

    async def translate_texts():
        tasks = []
        for page_texts in filtered_pdf_texts.values():
            for text in page_texts.texts:
                tasks.append(
                    get_text_translation(
                        text_translation_prompt_config,
                        text.text_id,
                        text.text,
                        input_language_config,
                        plate_language_config,
                    )
                )
                tasks.append(
                    get_text_translation(
                        text_translation_prompt_config,
                        easy_reads_by_text_id[text.text_id].easy_read_id,
                        easy_reads_by_text_id[text.text_id].easy_read,
                        input_language_config,
                        plate_language_config,
                    )
                )

        return await gather_with_limit(tasks, text_translation_prompt_config.rate_limit)

    texts = run_async_task(translate_texts)
    for t in texts:
        texts_by_id[t.text_id] = t
    return texts_by_id


def pdf_pages(run_output_dir_config: str, pdf_path_config: str, pdf_hash_config: str, page_range_config: PageRangeConfig) -> list[Page]:
    image_dir = os.path.join(run_output_dir_config, "images")
    return pages_for_pdf(image_dir, pdf_path_config, page_range_config.start, page_range_config.end)
