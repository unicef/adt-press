# mypy: ignore-errors
from banks import Prompt
from pydantic import ValidationInfo, field_validator

from adt_press.llm import format_model_name, get_instructor_client
from adt_press.models.config import PromptConfig
from adt_press.models.plate import PlateImage, PlateSection, PlateText
from adt_press.models.web import RenderTextGroup, WebPage
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.html import extract_formatted_texts, validate_generated_html_data_ids
from adt_press.utils.languages import LANGUAGE_MAP


class GenerationResponse(CleanTextBaseModel):
    reasoning: str
    content: str

    @field_validator("content")
    @classmethod
    def validate_html_data_ids(cls, v: str, info: ValidationInfo) -> str:
        """Sanitize and validate generated HTML content."""
        if not v or not v.strip():
            raise ValueError("Generated HTML content is empty.")

        # Get valid IDs from context
        text_ids = set()
        image_ids = set()
        section_type = None

        if info.context:
            text_ids.update(info.context.get("text_ids", []))
            image_ids.update(info.context.get("image_ids", []))
            section_type = info.context.get("section_type")

        # Use unified validation
        return validate_generated_html_data_ids(
            v,
            text_ids=text_ids,
            image_ids=image_ids,
            section_type=section_type,
            activity_rendering_enabled=True,
            allow_activity_generated_ids=False,
        )


async def generate_web_page_html(
    render_strategy: str,
    config: PromptConfig,
    examples: list[str],
    section: PlateSection,
    groups: list[RenderTextGroup],
    texts: list[PlateText],
    images: list[PlateImage],
    language_code: str,
) -> WebPage:
    language = LANGUAGE_MAP[language_code]

    context = dict(
        section=section,
        groups=[g.model_dump() for g in groups],
        texts=[t.model_dump() for t in texts],
        images=[i.model_dump() for i in images],
        language=language,
        examples=examples,
    )

    template_path = config.template_path
    prompt = Prompt(cached_read_text_file(template_path))

    client = get_instructor_client()

    # Create validation context for Pydantic
    validation_context = {
        "text_ids": [t.text_id for t in texts],
        "image_ids": [i.image_id for i in images],
        "section_type": section.section_type,
    }

    messages = [m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)]

    response: GenerationResponse = await client.chat.completions.create(
        model=format_model_name(config.model),
        response_model=GenerationResponse,
        messages=messages,
        max_retries=config.max_retries,
        context=validation_context,
        timeout=config.timeout,
    )

    # Extract formatted texts with inline HTML tags preserved
    formatted_texts = extract_formatted_texts(response.content)

    # The content is already sanitized and validated by the field_validator
    return WebPage(
        text_id=texts[0].text_id if texts else "",
        section_id=section.section_id,
        reasoning=response.reasoning,
        content=response.content,
        image_ids=[i.image_id for i in images],
        text_ids=[t.text_id for t in texts],
        render_strategy=render_strategy,
        formatted_texts=formatted_texts,  # Add this
    )
