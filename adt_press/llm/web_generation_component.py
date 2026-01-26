# mypy: ignore-errors
"""
Component-based web page generation.

This module generates web pages by selecting and populating components
from a pre-extracted design system, ensuring consistent styling.
"""

from banks import Prompt
from pydantic import ValidationInfo, field_validator

from adt_press.llm import get_instructor_client
from adt_press.models.config import PromptConfig
from adt_press.models.plate import PlateImage, PlateSection, PlateText
from adt_press.models.web import WebPage
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.html import extract_formatted_texts, validate_generated_html_data_ids
from adt_press.utils.languages import Language


class ComponentGenerationResponse(CleanTextBaseModel):
    """Response from component-based generation."""

    component_selected: str
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


async def generate_web_page_component(
    render_strategy: str,
    config: PromptConfig,
    section: PlateSection,
    texts: list[PlateText],
    images: list[PlateImage],
    language: Language,
    component_library: str,
) -> WebPage:
    """
    Generate a web page by selecting and populating a component.

    Args:
        render_strategy: The render strategy name
        config: Prompt configuration
        section: The section to render
        texts: Text elements to include
        images: Images to include
        language: Target language
        component_library: The component library markdown content
    """
    # Don't pass component_library to Banks - it contains { } that Jinja2 would interpret
    context = {
        "section": section,
        "texts": [t.model_dump() for t in texts],
        "images": [i.model_dump() for i in images],
        "language": language.name,
    }

    template_path = "prompts/web_generation_component.jinja2"
    prompt = Prompt(cached_read_text_file(template_path))

    client = get_instructor_client()

    # Create validation context for Pydantic
    validation_context = {
        "text_ids": [t.text_id for t in texts],
        "image_ids": [i.image_id for i in images],
        "section_type": section.section_type,
    }

    messages = [m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)]

    # Replace the placeholder with actual component library content AFTER Banks renders
    # Wrap in Jinja2 raw block to prevent Instructor's templating from parsing it
    # The component library contains { } # characters that Jinja2 would interpret
    placeholder = "__COMPONENT_LIBRARY_PLACEHOLDER__"
    # Wrap component library in raw block so Instructor's Jinja2 doesn't parse it
    safe_component_library = "{% raw %}" + component_library + "{% endraw %}"
    for msg in messages:
        if isinstance(msg.get("content"), str):
            msg["content"] = msg["content"].replace(placeholder, safe_component_library)
        elif isinstance(msg.get("content"), list):
            for part in msg["content"]:
                if isinstance(part, dict) and part.get("type") == "text":
                    part["text"] = part["text"].replace(placeholder, safe_component_library)

    response: ComponentGenerationResponse = await client.chat.completions.create(
        model=config.model,
        response_model=ComponentGenerationResponse,
        messages=messages,
        max_retries=config.max_retries,
        context=validation_context,
        timeout=config.timeout,
    )

    # Extract formatted texts with inline HTML tags preserved
    formatted_texts = extract_formatted_texts(response.content)

    return WebPage(
        text_id=texts[0].text_id if texts else "",
        section_id=section.section_id,
        reasoning=f"Component: {response.component_selected}. {response.reasoning}",
        content=response.content,
        image_ids=[i.image_id for i in images],
        text_ids=[t.text_id for t in texts],
        render_strategy=render_strategy,
        formatted_texts=formatted_texts,
    )
