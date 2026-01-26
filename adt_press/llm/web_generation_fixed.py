# mypy: ignore-errors
"""
Fixed template-based web page generation with slot filling.

This module generates web pages by selecting a fixed template and filling
its slots with content. Unlike the component-based approach, the LLM has
NO layout decisions to make - it only fills predefined slots.
"""

from banks import Prompt
from bs4 import BeautifulSoup, Comment, NavigableString
from pydantic import ValidationInfo, field_validator

from adt_press.llm import get_instructor_client
from adt_press.llm.template_extraction import (
    BookTemplateSet,
    PageTemplate,
    get_template_for_section,
)


def slot_styling_to_markdown(template: PageTemplate) -> str:
    """Generate markdown with slot styling for the current template only."""
    lines = [
        f"## Slot Styling for '{template.name}'",
        "",
        "**USE THESE EXACT STYLES when filling each slot:**",
        "",
    ]

    for slot in template.slots:
        lines.append(f"### `{{{slot.name}}}` ({slot.slot_type})")
        lines.append(f"- **Description**: {slot.description}")
        if slot.tailwind_classes:
            lines.append(f"- **REQUIRED Tailwind classes**: `{slot.tailwind_classes}`")
        if slot.custom_css:
            lines.append(f"- **Additional CSS**: `{slot.custom_css}`")
        lines.append(f"- **HTML pattern**:")
        lines.append(f"  ```html")
        lines.append(f"  {slot.html_wrapper}")
        lines.append(f"  ```")
        lines.append("")

    return "\n".join(lines)
from adt_press.models.config import PromptConfig
from adt_press.models.plate import PlateImage, PlateSection, PlateText
from adt_press.models.web import WebPage
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.html import extract_formatted_texts
from adt_press.utils.languages import Language


def validate_fixed_template_html(
    html_content: str,
    text_ids: set[str],
    image_ids: set[str],
) -> str:
    """Validate HTML from fixed templates - simpler validation without strict container requirements.

    Fixed templates have their own structure extracted from the book design,
    so we only validate data-ids, not container structure.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Strip document wrappers if LLM wrapped content in html/body tags
    if soup.body:
        html_content = "".join(str(child) for child in soup.body.contents)
        soup = BeautifulSoup(html_content, "html.parser")

    if not soup.find(True):
        raise ValueError("Generated HTML does not contain any HTML elements.")

    # Validate text elements - check data-ids are valid
    for element in soup.find_all(True):
        direct_text_nodes = []
        for child in element.children:
            if isinstance(child, Comment):
                continue
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    direct_text_nodes.append(text)

        if direct_text_nodes:
            data_id = element.get("data-id")
            if data_id and data_id not in text_ids:
                raise ValueError(
                    f"HTML element '{element.name}' has invalid data-id='{data_id}'. "
                    f"Must be one of text IDs: {', '.join(sorted(text_ids))}"
                )

    # Validate image elements
    for img_element in soup.find_all("img"):
        data_id = img_element.get("data-id")
        if not data_id:
            raise ValueError(
                f"Image element is missing required data-id attribute. "
                f"Image attributes: {dict(img_element.attrs)}"
            )
        if data_id not in image_ids:
            raise ValueError(
                f"Image element has invalid data-id='{data_id}'. "
                f"Must be one of image IDs: {', '.join(sorted(image_ids))}"
            )

    return str(soup)


class TemplateFilledResponse(CleanTextBaseModel):
    """Response from template slot filling."""

    template_used: str
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

        if info.context:
            text_ids.update(info.context.get("text_ids", []))
            image_ids.update(info.context.get("image_ids", []))

        # Use simpler validation for fixed templates - no strict container requirements
        return validate_fixed_template_html(
            v,
            text_ids=text_ids,
            image_ids=image_ids,
        )


async def generate_web_page_fixed(
    render_strategy: str,
    config: PromptConfig,
    section: PlateSection,
    texts: list[PlateText],
    images: list[PlateImage],
    language: Language,
    book_templates: BookTemplateSet,
) -> WebPage:
    """
    Generate a web page by filling slots in a fixed template.

    The key difference from component-based generation:
    - Template is SELECTED based on section type (no LLM decision)
    - LLM ONLY fills the slots with content
    - No layout decisions = consistent results
    """
    # Get the template for this section type
    template = get_template_for_section(book_templates, section.section_type)
    if not template:
        raise ValueError(f"No template found for section type: {section.section_type}")

    # Build context - don't pass templates through Jinja2
    context = {
        "section": section,
        "texts": [t.model_dump() for t in texts],
        "images": [i.model_dump() for i in images],
        "language": language.name,
        "template_name": template.name,
        "section_type": section.section_type,
    }

    template_path = "prompts/web_generation_fixed.jinja2"
    prompt = Prompt(cached_read_text_file(template_path))

    client = get_instructor_client()

    # Create validation context for Pydantic
    validation_context = {
        "text_ids": [t.text_id for t in texts],
        "image_ids": [i.image_id for i in images],
        "section_type": section.section_type,
    }

    messages = [m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)]

    # Replace placeholders with actual content AFTER Banks renders
    # Wrap in raw block to prevent Instructor's Jinja2 from parsing
    template_placeholder = "__TEMPLATE_PLACEHOLDER__"
    slot_styling_placeholder = "__SLOT_STYLING_PLACEHOLDER__"

    template_html = "{% raw %}" + template.html_template + "{% endraw %}"
    slot_styling = "{% raw %}" + slot_styling_to_markdown(template) + "{% endraw %}"

    for msg in messages:
        if isinstance(msg.get("content"), str):
            msg["content"] = msg["content"].replace(template_placeholder, template_html)
            msg["content"] = msg["content"].replace(slot_styling_placeholder, slot_styling)
        elif isinstance(msg.get("content"), list):
            for part in msg["content"]:
                if isinstance(part, dict) and part.get("type") == "text":
                    part["text"] = part["text"].replace(template_placeholder, template_html)
                    part["text"] = part["text"].replace(slot_styling_placeholder, slot_styling)

    response: TemplateFilledResponse = await client.chat.completions.create(
        model=config.model,
        response_model=TemplateFilledResponse,
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
        reasoning=f"Template: {response.template_used}",
        content=response.content,
        image_ids=[i.image_id for i in images],
        text_ids=[t.text_id for t in texts],
        render_strategy=render_strategy,
        formatted_texts=formatted_texts,
    )
