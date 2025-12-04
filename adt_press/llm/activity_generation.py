# mypy: ignore-errors
from typing import Any

from banks import Prompt

from adt_press.llm import get_instructor_client
from adt_press.models.activity import Activity, ActivityType
from adt_press.models.config import PromptConfig
from adt_press.models.image import ProcessedImage
from adt_press.models.pdf import Page
from adt_press.models.section import PageSection
from adt_press.models.text import PageText
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file


class ActivityGenerationResponse(CleanTextBaseModel):
    reasoning: str
    items: list[dict[str, Any]]


async def generate_activity_definition(
    config: PromptConfig,
    page: Page,
    section: PageSection,
    texts: list[PageText],
    images: list[ProcessedImage],
    activity_type: ActivityType,
) -> Activity:
    """
    Generate an activity definition using the LLM.

    Uses the prompt template specified in the config's template_path.

    Args:
        config: Prompt configuration (model, template_path, rate_limit, max_retries)
        page: The PDF page containing the section
        section: The section to generate activity for
        texts: List of PageText objects with text_id and text content
        images: List of ProcessedImage objects with image_id and image_path
        activity_type: Type of activity to generate

    Returns:
        Activity object with generated definition
    """
    context = dict(
        page=page,
        section=section,
        texts=[t.model_dump() for t in texts],
        images=[i.model_dump() for i in images],
        activity_type=activity_type.value,
        examples=config.examples if hasattr(config, "examples") else [],
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = get_instructor_client()

    response: ActivityGenerationResponse = await client.chat.completions.create(
        model=config.model,
        response_model=ActivityGenerationResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
    )

    return Activity(
        activity_id=f"act_{section.section_id}",
        section_id=section.section_id,
        activity_type=activity_type,
        items=response.items,
        reasoning=response.reasoning,
    )
