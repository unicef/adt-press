# mypy: ignore-errors
"""
Manifest-based web page generation with consistent styling.

This module generates web pages using a content manifest and style map.
The LLM receives the style map and content, and must apply styling consistently.
"""

from banks import Prompt
from bs4 import BeautifulSoup, Comment, NavigableString
from pydantic import ValidationInfo, field_validator

from adt_press.llm import get_instructor_client
from adt_press.llm.content_manifest import (
    DEFAULT_STYLE_MAP,
    IMAGE_STYLES,
    StyleRule,
    generate_section_html,
    get_layout_for_section_type,
    get_style_for_text_type,
)
from adt_press.models.config import PromptConfig
from adt_press.models.plate import PlateGroup, PlateImage, PlateSection, PlateText
from adt_press.models.web import WebPage
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.html import extract_formatted_texts
from adt_press.utils.languages import Language


def validate_manifest_html(
    html_content: str,
    text_ids: set[str],
    image_ids: set[str],
) -> str:
    """Validate HTML from manifest-based generation."""
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


class ManifestPageResponse(CleanTextBaseModel):
    """Response from manifest-based page generation."""

    content: str

    @field_validator("content")
    @classmethod
    def validate_html_data_ids(cls, v: str, info: ValidationInfo) -> str:
        """Sanitize and validate generated HTML content."""
        if not v or not v.strip():
            raise ValueError("Generated HTML content is empty.")

        text_ids = set()
        image_ids = set()

        if info.context:
            text_ids.update(info.context.get("text_ids", []))
            image_ids.update(info.context.get("image_ids", []))

        return validate_manifest_html(v, text_ids=text_ids, image_ids=image_ids)


def generate_style_map_markdown(style_map: dict[str, StyleRule] | None = None) -> str:
    """Generate markdown representation of the style map."""
    if style_map is None:
        style_map = DEFAULT_STYLE_MAP

    lines = [
        "# STYLE MAP - USE THESE EXACT STYLES",
        "",
        "## Text Styling (MANDATORY)",
        "",
        "| Text Type | Element | Tailwind Classes |",
        "|-----------|---------|------------------|",
    ]

    for text_type, rule in style_map.items():
        lines.append(f"| `{text_type}` | `<{rule.html_element}>` | `{rule.tailwind_classes}` |")

    lines.extend([
        "",
        "## Image Styling (MANDATORY)",
        "",
        f"- **Single image:** `{IMAGE_STYLES['single']}`",
        f"- **Multiple images:** each gets `{IMAGE_STYLES['multiple']}`",
        f"- **Image grid container:** `{IMAGE_STYLES['grid']}`",
        "",
    ])

    return "\n".join(lines)


def generate_content_for_section(
    section: PlateSection,
    texts: list[PlateText],
    images: list[PlateImage],
    groups: list[PlateGroup],
) -> str:
    """Generate content markdown for a section.

    IMPORTANT: Respects part_ids order to preserve the natural flow of
    text and images as they appear in the original book.
    """
    layout_hint = getattr(section, 'layout_hint', 'stacked')

    lines = [
        f"# Section Content: {section.section_id}",
        f"**Section Type:** `{section.section_type}`",
        f"**Layout:** `{layout_hint}`",
        "",
    ]

    layout = get_layout_for_section_type(section.section_type)
    lines.extend([
        "## Layout Structure",
        f"- Outer background: `{layout['bg_class']}`",
        f"- Container: `{layout['container_class']}`",
        f"- Content panel: `{layout['content_class']}`",
        "",
    ])

    # Add layout-specific instructions
    if layout_hint == "text_left_image_right":
        lines.extend([
            "## Layout Instructions: TEXT LEFT, IMAGE RIGHT",
            "Use a two-column flexbox layout:",
            "- `<div class=\"flex flex-col md:flex-row gap-8\">`",
            "- Left column (text): `<div class=\"flex-1 space-y-4\">` containing all text elements",
            "- Right column (images): `<div class=\"flex-1 space-y-4\">` containing all images",
            "",
        ])
    elif layout_hint == "image_left_text_right":
        lines.extend([
            "## Layout Instructions: IMAGE LEFT, TEXT RIGHT",
            "Use a two-column flexbox layout:",
            "- `<div class=\"flex flex-col md:flex-row gap-8\">`",
            "- Left column (images): `<div class=\"flex-1 space-y-4\">` containing all images",
            "- Right column (text): `<div class=\"flex-1 space-y-4\">` containing all text elements",
            "",
        ])
    elif layout_hint == "image_top":
        lines.extend([
            "## Layout Instructions: IMAGE TOP",
            "Place image(s) at the top, text below:",
            "- Image(s) first with `mb-6` margin",
            "- Text content below in `<div class=\"space-y-4\">`",
            "",
        ])
    elif layout_hint == "grid_images":
        lines.extend([
            "## Layout Instructions: GRID IMAGES",
            "Text first, then images in a grid:",
            "- Text in `<div class=\"space-y-4 mb-6\">`",
            "- Images in `<div class=\"grid grid-cols-2 gap-4\">`",
            "",
        ])
    elif layout_hint == "two_column_text":
        lines.extend([
            "## Layout Instructions: TWO COLUMN TEXT",
            "Split text into two columns:",
            "- `<div class=\"flex flex-col md:flex-row gap-8\">`",
            "- Split text elements roughly in half between two `<div class=\"flex-1 space-y-4\">` columns",
            "- Images (if any) go below the columns",
            "",
        ])
    else:  # stacked
        lines.extend([
            "## Layout Instructions: STACKED (VERTICAL)",
            "Stack content vertically in order:",
            "- Follow the numbered content order exactly",
            "- Add `mt-6` margin to images",
            "",
        ])

    lines.extend([
        "## Content (in display order)",
        "",
        "**IMPORTANT: Generate HTML elements following the layout instructions above.**",
        "",
    ])

    # Build lookup tables
    texts_by_id = {t.text_id: t for t in texts}
    images_by_id = {i.image_id: i for i in images}
    groups_by_id = {g.group_id: g for g in groups}
    processed_text_ids: set[str] = set()

    # Process items in the order they appear in part_ids
    item_number = 1
    for part_id in section.part_ids:
        # Check if it's a group
        if part_id in groups_by_id:
            group = groups_by_id[part_id]
            lines.append(f"### {item_number}. Group: `{group.group_id}` (type: `{group.group_type}`)")
            lines.append("Wrap these texts together in a `<div class=\"space-y-4\">`:")
            for text_id in group.text_ids:
                if text_id in texts_by_id:
                    text = texts_by_id[text_id]
                    style = get_style_for_text_type(text.text_type)
                    lines.append(f"- `{text.text_id}` (type: `{text.text_type}`)")
                    lines.append(f"  - Element: `<{style.html_element}>`")
                    lines.append(f"  - Classes: `{style.tailwind_classes}`")
                    lines.append(f"  - Text: \"{text.text}\"")
                    processed_text_ids.add(text_id)
            lines.append("")
            item_number += 1

        # Check if it's a text
        elif part_id in texts_by_id and part_id not in processed_text_ids:
            text = texts_by_id[part_id]
            style = get_style_for_text_type(text.text_type)
            lines.append(f"### {item_number}. Text: `{text.text_id}` (type: `{text.text_type}`)")
            lines.append(f"- Element: `<{style.html_element}>`")
            lines.append(f"- Classes: `{style.tailwind_classes}`")
            lines.append(f"- Text: \"{text.text}\"")
            lines.append("")
            processed_text_ids.add(part_id)
            item_number += 1

        # Check if it's an image
        elif part_id in images_by_id:
            img = images_by_id[part_id]
            lines.append(f"### {item_number}. Image: `{img.image_id}`")
            lines.append(f"- src: `images/{img.image_id}.jpg`")
            lines.append(f"- Classes: `{IMAGE_STYLES['single']} mt-6`")
            lines.append("")
            item_number += 1

    return "\n".join(lines)


async def generate_web_page_manifest(
    render_strategy: str,
    config: PromptConfig,
    section: PlateSection,
    texts: list[PlateText],
    images: list[PlateImage],
    groups: list[PlateGroup],
    language: Language,
    use_llm: bool = True,
) -> WebPage:
    """
    Generate a web page using the content manifest approach.

    If use_llm is False, generates HTML deterministically without an LLM.
    If use_llm is True, uses an LLM with the style map for more flexible layouts.
    """
    if not use_llm:
        # Deterministic generation - no LLM needed
        content = generate_section_html(section, texts, images, groups)
        return WebPage(
            text_id=texts[0].text_id if texts else "",
            section_id=section.section_id,
            reasoning="Deterministic manifest-based generation",
            content=content,
            image_ids=[i.image_id for i in images],
            text_ids=[t.text_id for t in texts],
            render_strategy=render_strategy,
            formatted_texts={},
        )

    # LLM-based generation with style map
    style_map_md = generate_style_map_markdown()
    content_md = generate_content_for_section(section, texts, images, groups)
    layout = get_layout_for_section_type(section.section_type)

    context = {
        "section": section,
        "texts": [t.model_dump() for t in texts],
        "images": [i.model_dump() for i in images],
        "groups": [g.model_dump() for g in groups],
        "language": language.name,
        "section_type": section.section_type,
    }

    template_path = "prompts/web_generation_manifest.jinja2"
    prompt = Prompt(cached_read_text_file(template_path))

    client = get_instructor_client()

    validation_context = {
        "text_ids": [t.text_id for t in texts],
        "image_ids": [i.image_id for i in images],
        "section_type": section.section_type,
    }

    messages = [m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)]

    # Replace placeholders
    style_map_placeholder = "__STYLE_MAP_PLACEHOLDER__"
    content_placeholder = "__CONTENT_PLACEHOLDER__"
    layout_placeholder = "__LAYOUT_PLACEHOLDER__"

    style_map_wrapped = "{% raw %}" + style_map_md + "{% endraw %}"
    content_wrapped = "{% raw %}" + content_md + "{% endraw %}"
    layout_wrapped = "{% raw %}" + f"""
- Outer: `<div class="min-h-[calc(100dvh-100px)] flex justify-center items-start {layout['bg_class']}">`
- Section: `<section role="article" data-section-type="{section.section_type}" class="relative {layout['container_class']}">`
- Content panel: `<div class="relative {layout['content_class']}">`
""" + "{% endraw %}"

    for msg in messages:
        if isinstance(msg.get("content"), str):
            msg["content"] = msg["content"].replace(style_map_placeholder, style_map_wrapped)
            msg["content"] = msg["content"].replace(content_placeholder, content_wrapped)
            msg["content"] = msg["content"].replace(layout_placeholder, layout_wrapped)
        elif isinstance(msg.get("content"), list):
            for part in msg["content"]:
                if isinstance(part, dict) and part.get("type") == "text":
                    part["text"] = part["text"].replace(style_map_placeholder, style_map_wrapped)
                    part["text"] = part["text"].replace(content_placeholder, content_wrapped)
                    part["text"] = part["text"].replace(layout_placeholder, layout_wrapped)

    response: ManifestPageResponse = await client.chat.completions.create(
        model=config.model,
        response_model=ManifestPageResponse,
        messages=messages,
        max_retries=config.max_retries,
        context=validation_context,
        timeout=config.timeout,
    )

    formatted_texts = extract_formatted_texts(response.content)

    return WebPage(
        text_id=texts[0].text_id if texts else "",
        section_id=section.section_id,
        reasoning="Manifest-based generation with style map",
        content=response.content,
        image_ids=[i.image_id for i in images],
        text_ids=[t.text_id for t in texts],
        render_strategy=render_strategy,
        formatted_texts=formatted_texts,
    )
