"""LLM-based web page editing functionality."""

from banks import Prompt

from adt_press.llm import get_instructor_client
from adt_press.models.config import HTMLPromptConfig
from adt_press.models.ids import SectionID
from adt_press.models.plate import PlateSection
from adt_press.models.web import WebPage
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.languages import Language


class WebEditResponse(CleanTextBaseModel):
    """Response from web page edit LLM call."""

    html: str
    reasoning: str


async def edit_web_page_with_llm(
    section_id: SectionID,
    existing_page: WebPage,
    edit_instruction: str,
    section: PlateSection,
    config: HTMLPromptConfig,
    language: Language,
) -> WebPage:
    """
    Edit an existing web page using LLM based on user instruction.

    Args:
        section_id: The section ID being edited
        existing_page: The current WebPage object
        edit_instruction: User's instruction for how to modify the page (e.g., "make the title bigger")
        section: The PlateSection metadata
        config: Configuration for the LLM call
        language: Language for the page

    Returns:
        Updated WebPage with modified content
    """
    prompt = Prompt(cached_read_text_file(config.template_path))

    context = dict(
        section_id=section_id,
        existing_html=existing_page.content,
        edit_instruction=edit_instruction,
        section_type=section.section_type,
        page_number=section.page_number,
        language=language.name,
    )

    client = get_instructor_client()
    response: WebEditResponse = await client.chat.completions.create(
        model=config.model,
        response_model=WebEditResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
        timeout=config.timeout,
    )

    # Return updated WebPage with new content and reasoning
    return WebPage(
        section_id=existing_page.section_id,
        text_id=existing_page.text_id,
        text_ids=existing_page.text_ids,
        image_ids=existing_page.image_ids,
        generated_texts=existing_page.generated_texts,
        content=response.html,
        reasoning=f"EDIT: {edit_instruction} | {response.reasoning}",
        render_strategy=existing_page.render_strategy,
        activity_answers=existing_page.activity_answers,
        activity_reasoning=existing_page.activity_reasoning,
        formatted_texts=existing_page.formatted_texts,
    )
