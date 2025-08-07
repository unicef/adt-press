import os

from adt_press.data.image import Image
from adt_press.data.pdf import Page
from adt_press.data.text import OutputText, PageText, PageTexts
from adt_press.llm.prompt import PromptConfig
from adt_press.llm.text_extraction import get_page_text
from adt_press.llm.text_translation import get_text_translation
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
                    type=t.type,
                    is_pruned=t.type in pruned_text_types_config,
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
    input_language_config: str,
    output_language_config: str,
) -> dict[str, OutputText]:
    texts_by_id = {}

    # noop if input and output languages are the same
    if input_language_config == output_language_config:
        for page_texts in filtered_pdf_texts.values():
            for text in page_texts.texts:
                texts_by_id[text.text_id] = OutputText(
                    text_id=text.text_id,
                    text=text.text,
                    language_code=input_language_config,
                    reasoning="",
                )
        return texts_by_id

    async def translate_texts():
        tasks = []
        for page_texts in filtered_pdf_texts.values():
            for text in page_texts.texts:
                tasks.append(
                    get_text_translation(
                        text_translation_prompt_config,
                        text,
                        input_language_config,
                        output_language_config,
                    )
                )

        return await gather_with_limit(tasks, text_translation_prompt_config.rate_limit)

    texts = run_async_task(translate_texts)
    for t in texts:
        texts_by_id[t.text_id] = t
    return texts_by_id


def pdf_pages(output_dir_config: str, pdf_path_config: str, pdf_hash_config: str, page_range_config: PageRangeConfig) -> list[Page]:
    image_dir = os.path.join(output_dir_config, "images")
    return pages_for_pdf(image_dir, pdf_path_config, page_range_config.start, page_range_config.end)
