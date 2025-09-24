from hamilton.function_modifiers import config

from adt_press.llm.text_easy_read import get_text_easy_read
from adt_press.llm.text_extraction import get_page_text
from adt_press.models.config import PromptConfig
from adt_press.models.image import Image
from adt_press.models.pdf import Page
from adt_press.models.text import EasyReadText, PageText, PageTextGroup, PageTexts
from adt_press.nodes.config_nodes import PageRangeConfig
from adt_press.utils.pdf import pages_for_pdf
from adt_press.utils.sync import gather_with_limit, run_async_task


def pdf_pages_by_id(pdf_pages: list[Page]) -> dict[str, Page]:
    return {p.page_id: p for p in pdf_pages}


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

    texts = {pt.page_id: pt for pt in run_async_task(extract_text)}
    return texts


@config.when(easy_read_strategy="llm")
def easy_reads_by_text_id__llm(
    input_language_config: str,
    text_easy_read_prompt_config: PromptConfig,
    processed_pdf_texts: dict[str, PageTexts],
) -> dict[str, EasyReadText]:
    async def get_easy_reads():
        tasks = []
        for page_texts in processed_pdf_texts.values():
            for text in page_texts.texts:
                tasks.append(get_text_easy_read(input_language_config, text_easy_read_prompt_config, text))

        return await gather_with_limit(tasks, text_easy_read_prompt_config.rate_limit)

    results = run_async_task(get_easy_reads)
    return {easy_read.text_id: easy_read for easy_read in results}


@config.when(easy_read_strategy="none")
def easy_reads_by_text_id__none(
    input_language_config: str,
    text_easy_read_prompt_config: PromptConfig,
    processed_pdf_texts: dict[str, PageTexts],
) -> dict[str, EasyReadText]:
    return {}


def processed_pdf_texts(pruned_text_types_config: list[str], pdf_texts: dict[str, PageTexts]) -> dict[str, PageTexts]:
    filtered_texts = {}
    for page_id, page_texts in pdf_texts.items():
        groups = []
        for g in page_texts.groups:
            group_texts = [PageText(
                    text_id=t.text_id,
                    text=t.text,
                    text_type=t.text_type,
                    is_pruned=t.text_type in pruned_text_types_config,
                )
                for t in g.texts]
            
            groups.append(PageTextGroup(
                group_id=g.group_id,
                group_type=g.group_type,
                texts=group_texts
            ))

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
                groups.append(PageTextGroup(
                    group_id=g.group_id,
                    group_type=g.group_type,
                    texts=group_texts
                ))

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

def pdf_pages(run_output_dir_config: str, pdf_path_config: str, pdf_hash_config: str, page_range_config: PageRangeConfig) -> list[Page]:
    return pages_for_pdf(run_output_dir_config, pdf_path_config, page_range_config.start, page_range_config.end)
