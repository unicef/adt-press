from hamilton.function_modifiers import config

from adt_press.llm.page_sectioning import get_page_sections
from adt_press.llm.section_explanations import get_section_explanation
from adt_press.llm.section_glossary import get_section_glossary
from adt_press.llm.section_quiz import generate_quiz
from adt_press.models.config import PromptConfig, QuizPromptConfig, SectionType
from adt_press.models.image import ProcessedImage
from adt_press.models.pdf import Page
from adt_press.models.section import PageSection, PageSections, SectionExplanation, SectionGlossary, SectionQuiz
from adt_press.models.text import PageText, PageTextGroup, PageTexts
from adt_press.utils.sync import gather_with_limit, run_async_task


def sections_by_page_id(
    pdf_pages: list[Page],
    processed_images_by_page: dict[str, list[ProcessedImage]],
    filtered_pdf_texts: dict[str, PageTexts],
    page_sectioning_prompt_config: PromptConfig,
    section_types_config: dict[str, SectionType],
    page_grouping_config: str,
) -> dict[str, PageSections]:
    page_sections = {}

    spread_mode = page_grouping_config == "spread"

    async def section_pages():
        sections = []
        for page in pdf_pages:
            page_images = processed_images_by_page[page.page_id]
            page_texts = filtered_pdf_texts[page.page_id]

            # if we didn't extract any good images or text, we skip sectioning this page
            if not page_images and not page_texts.groups:
                page_sections[page.page_id] = PageSections(page_id=page.page_id, sections=[], reasoning="No images or text to section")
            else:
                sections.append(
                    get_page_sections(
                        page_sectioning_prompt_config, section_types_config, spread_mode, page, page_images, page_texts.groups
                    )
                )

        return await gather_with_limit(sections, page_sectioning_prompt_config.rate_limit)

    sections = run_async_task(section_pages)
    for p in sections:
        page_sections[p.page_id] = p
    return page_sections


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
                    page_number=section.page_number,
                    part_ids=section.part_ids,
                    background_color=section.background_color,
                    text_color=section.text_color,
                    is_pruned=section.section_type in pruned_section_types_config,
                )
                for section in page_sections.sections
            ],
            reasoning=page_sections.reasoning,
        )
    return filtered_sections


def quizzes_by_section_id(
        plate_language_config: str,
        pdf_pages: list[Page],
        filtered_sections_by_page_id: dict[str, PageSections],
        pdf_text_groups_by_id: dict[str, PageTextGroup],
        quiz_prompt_config: QuizPromptConfig) -> dict[str, SectionQuiz]:

    # noop if your config says 0 sections per quiz
    if quiz_prompt_config.sections_per_quiz < 1:
        return {}

    async def get_quizzes():
        tasks = []
        sections = []
        count = 0
        quizzes: dict[str, SectionQuiz] = {}
        for page in pdf_pages:
            page_sections = filtered_sections_by_page_id[page.page_id]
            for section in page_sections.sections:
                if section.is_pruned:
                    continue

                count += 1
                sections.append(section)

                if count == quiz_prompt_config.sections_per_quiz:
                    tasks.append(generate_quiz(quiz_prompt_config, sections, pdf_text_groups_by_id))
                    sections = []
                    count = 0

        return await gather_with_limit(tasks, quiz_prompt_config.rate_limit)
        
    results = run_async_task(get_quizzes)
    return {quiz.section_id: quiz for quiz in results}

@config.when(explanation_strategy="llm")
def explanations_by_section_id__llm(
    plate_language_config: str,
    pdf_pages: list[Page],
    filtered_sections_by_page_id: dict[str, PageSections],
    processed_pdf_texts_by_id: dict[str, PageText],
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
                    text = processed_pdf_texts_by_id.get(part_id)
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


@config.when(explanation_strategy="none")
def explanations_by_section_id__none(
    plate_language_config: str,
    pdf_pages: list[Page],
    filtered_sections_by_page_id: dict[str, PageSections],
    processed_pdf_texts_by_id: dict[str, PageText],
    processed_images_by_id: dict[str, ProcessedImage],
    section_explanation_prompt_config: PromptConfig,
) -> dict[str, SectionExplanation]:
    return {}


@config.when(glossary_strategy="llm")
def section_glossaries_by_id__llm(
    plate_language_config: str,
    section_glossary_prompt_config: PromptConfig,
    filtered_sections_by_page_id: dict[str, PageSections],
    pdf_text_groups_by_id: dict[str, PageTextGroup],
) -> dict[str, SectionGlossary]:
    async def get_glossaries():
        tasks = []
        for page_sections in filtered_sections_by_page_id.values():
            for section in filter(lambda s: not s.is_pruned, page_sections.sections):
                texts = []
                for part_id in section.part_ids:
                    if part_id.startswith("grp_"):
                        group = pdf_text_groups_by_id[part_id]
                        texts.extend([t.text for t in group.texts])
                tasks.append(get_section_glossary(plate_language_config, section_glossary_prompt_config, section, texts))

        return await gather_with_limit(tasks, section_glossary_prompt_config.rate_limit)

    results = run_async_task(get_glossaries)
    return {glossary.section_id: glossary for glossary in results}


@config.when(glossary_strategy="none")
def section_glossaries_by_id__none(
    plate_language_config: str,
    section_glossary_prompt_config: PromptConfig,
    filtered_sections_by_page_id: dict[str, PageSections],
    processed_pdf_texts_by_id: dict[str, PageText],
) -> dict[str, SectionGlossary]:
    return {}
