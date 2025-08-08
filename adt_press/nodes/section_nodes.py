from adt_press.llm.page_sectioning import get_page_sections
from adt_press.llm.section_easy_read import get_section_easy_read
from adt_press.llm.section_explanations import get_section_explanation
from adt_press.llm.section_glossary import get_section_glossary
from adt_press.models.config import PromptConfig
from adt_press.models.image import ProcessedImage
from adt_press.models.pdf import Page
from adt_press.models.section import PageSection, PageSections, SectionEasyRead, SectionExplanation, SectionGlossary
from adt_press.models.text import OutputText, PageText, PageTexts
from adt_press.utils.sync import gather_with_limit, run_async_task


def sections_by_page_id(
    pdf_pages: list[Page],
    processed_images_by_page: dict[str, list[ProcessedImage]],
    filtered_pdf_texts: dict[str, PageTexts],
    page_sectioning_prompt_config: PromptConfig,
) -> dict[str, PageSections]:
    page_sections = {}

    async def section_pages():
        sections = []
        for page in pdf_pages:
            page_images = processed_images_by_page[page.page_id]
            page_texts = [t for t in filtered_pdf_texts[page.page_id].texts if not t.is_pruned]

            # if we didn't extract any good images or text, we skip sectioning this page
            if not page_images and not page_texts:
                page_sections[page.page_id] = PageSections(page_id=page.page_id, sections=[], reasoning="No images or text to section")
            else:
                sections.append(get_page_sections(page_sectioning_prompt_config, page, page_images, page_texts))

        return await gather_with_limit(sections, page_sectioning_prompt_config.rate_limit)

    sections = run_async_task(section_pages)
    for p in sections:
        page_sections[p.page_id] = p
    return page_sections


def filtered_sections_by_section_id(filtered_sections_by_page_id: dict[str, PageSections]) -> dict[str, PageSection]:
    return {s.section_id: s for page_sections in filtered_sections_by_page_id.values() for s in page_sections.sections}


def filtered_sections_by_page_id(
    pruned_section_types_config: list[str], sections_by_page_id: dict[str, PageSections]
) -> dict[str, PageSections]:
    filtered_sections = {}
    for page_id, page_sections in sections_by_page_id.items():
        filtered_sections[page_id] = PageSections(
            page_id=page_id,
            sections=[
                PageSection(
                    section_id=section.section_id,
                    section_type=section.section_type,
                    part_ids=section.part_ids,
                    is_pruned=section.section_type in pruned_section_types_config,
                )
                for section in page_sections.sections
            ],
            reasoning=page_sections.reasoning,
        )
    return filtered_sections


def explanations_by_section_id(
    plate_language_config: str,
    pdf_pages: list[Page],
    filtered_sections_by_page_id: dict[str, PageSections],
    filtered_pdf_texts_by_id: dict[str, PageText],
    processed_images_by_id: dict[str, ProcessedImage],
    section_explanation_prompt_config: PromptConfig,
) -> dict[str, SectionExplanation]:
    async def explain_sections():
        explanations = []
        for page in pdf_pages:
            page_sections = filtered_sections_by_page_id[page.page_id]
            for section in filter(lambda s: not s.is_pruned, page_sections.sections):
                texts = []
                images: list[ProcessedImage] = []

                for part_id in section.part_ids:
                    text = filtered_pdf_texts_by_id.get(part_id)
                    texts.extend([text.text] if text else [])
                    image = processed_images_by_id.get(part_id)
                    images.extend([image] if image else [])

                explanations.append(
                    get_section_explanation(section_explanation_prompt_config, page, section, texts, images, plate_language_config)
                )

        return await gather_with_limit(explanations, section_explanation_prompt_config.rate_limit)

    explanations: dict[str, SectionExplanation] = {}
    results = run_async_task(explain_sections)
    for explanation in results:
        explanations[explanation.section_id] = explanation

    return explanations


def section_glossaries_by_id(
    plate_language_config: str,
    section_glossary_prompt_config: PromptConfig,
    filtered_sections_by_page_id: dict[str, PageSections],
    output_pdf_texts_by_id: dict[str, OutputText],
) -> dict[str, SectionGlossary]:
    async def get_glossaries():
        tasks = []
        for page_sections in filtered_sections_by_page_id.values():
            for section in filter(lambda s: not s.is_pruned, page_sections.sections):
                texts = [output_pdf_texts_by_id[part_id].text for part_id in section.part_ids if part_id.startswith("txt_")]
                tasks.append(get_section_glossary(plate_language_config, section_glossary_prompt_config, section, texts))

        return await gather_with_limit(tasks, section_glossary_prompt_config.rate_limit)

    results = run_async_task(get_glossaries)
    return {glossary.section_id: glossary for glossary in results}


def section_easy_reads_by_id(
    plate_language_config: str,
    section_easy_read_prompt_config: PromptConfig,
    filtered_sections_by_page_id: dict[str, PageSections],
    output_pdf_texts_by_id: dict[str, OutputText],
) -> dict[str, SectionEasyRead]:
    async def get_easy_reads():
        tasks = []
        for page_sections in filtered_sections_by_page_id.values():
            for section in filter(lambda s: not s.is_pruned, page_sections.sections):
                texts = [output_pdf_texts_by_id[part_id].text for part_id in section.part_ids if part_id.startswith("txt_")]
                tasks.append(get_section_easy_read(plate_language_config, section_easy_read_prompt_config, section, texts))

        return await gather_with_limit(tasks, section_easy_read_prompt_config.rate_limit)

    results = run_async_task(get_easy_reads)
    return {easy_read.section_id: easy_read for easy_read in results}
