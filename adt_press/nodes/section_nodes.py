from adt_press.llm.page_sectioning import get_page_sections
from adt_press.llm.prompt import PromptConfig
from adt_press.llm.section_explanations import get_section_explanation
from adt_press.utils.image import ProcessedImage
from adt_press.utils.pdf import Page, PageSections, PageText, PageTexts, SectionExplanation
from adt_press.utils.sync import gather_with_limit, run_async_task


def sections_by_page_id(
    pdf_pages: list[Page],
    processed_images_by_page: dict[str, list[ProcessedImage]],
    pdf_texts: dict[str, PageTexts],
    page_sectioning_prompt_config: PromptConfig,
) -> dict[str, PageSections]:
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


def explanations_by_section_id(
    output_language_config: str,
    pdf_pages: list[Page],
    sections_by_page_id: dict[str, PageSections],
    pdf_texts_by_id: dict[str, PageText],
    processed_images_by_id: dict[str, ProcessedImage],
    section_explanation_prompt_config: PromptConfig,
) -> dict[str, SectionExplanation]:
    async def explain_sections():
        explanations = []
        for page in pdf_pages:
            page_sections = sections_by_page_id[page.page_id]
            for section in page_sections.sections:
                texts = []
                images: list[ProcessedImage] = []

                for part_id in section.part_ids:
                    text = pdf_texts_by_id.get(part_id)
                    texts.extend([text.text] if text else [])
                    image = processed_images_by_id.get(part_id)
                    images.extend([image] if image else [])

                explanations.append(
                    get_section_explanation(section_explanation_prompt_config, page, section, texts, images, output_language_config)
                )

        return await gather_with_limit(explanations, section_explanation_prompt_config.rate_limit)

    explanations: dict[str, SectionExplanation] = {}
    results = run_async_task(explain_sections)
    for explanation in results:
        explanations[explanation.section_id] = explanation

    return explanations
