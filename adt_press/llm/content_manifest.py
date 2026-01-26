# mypy: ignore-errors
"""
Content manifest generation for consistent styling.

This module generates a content manifest that contains all book content
structured by sections, with a consistent style map applied across the entire book.
No vision model needed - styling is rule-based.
"""

from dataclasses import dataclass

from adt_press.models.plate import Plate, PlateGroup, PlateImage, PlateSection, PlateText


@dataclass
class StyleRule:
    """A styling rule for a text type or element."""

    html_element: str
    tailwind_classes: str
    wrapper_classes: str = ""  # For wrapping multiple elements


# Default style map - text_type to styling
DEFAULT_STYLE_MAP: dict[str, StyleRule] = {
    # Headings
    "book_title": StyleRule("h1", "text-4xl md:text-5xl font-extrabold text-black leading-tight"),
    "book_subtitle": StyleRule("h2", "text-2xl md:text-3xl font-semibold text-gray-700 leading-snug"),
    "section_heading": StyleRule("h1", "text-3xl md:text-4xl font-bold text-black leading-tight"),
    "chapter_title": StyleRule("h1", "text-4xl md:text-5xl font-extrabold text-black leading-tight"),
    "activity_title": StyleRule("h2", "text-2xl md:text-3xl font-bold text-black leading-tight"),

    # Body text
    "section_text": StyleRule("p", "text-lg md:text-xl leading-relaxed text-black"),
    "instruction_text": StyleRule("p", "text-base md:text-lg leading-relaxed text-gray-700 italic"),
    "standalone_text": StyleRule("p", "text-base md:text-lg leading-relaxed text-black"),

    # Metadata and captions
    "book_author": StyleRule("p", "text-lg text-gray-600"),
    "book_metadata": StyleRule("p", "text-sm text-gray-500"),
    "image_associated_text": StyleRule("p", "text-sm md:text-base text-gray-600 italic"),
    "image_overlay": StyleRule("span", "text-sm font-medium"),

    # Activity elements
    "activity_number": StyleRule("span", "text-xl font-bold text-black"),
    "activity_option": StyleRule("p", "text-base md:text-lg text-black"),
    "activity_input_placeholder_text": StyleRule("span", "text-base text-gray-400 italic"),
    "fill_in_the_blank": StyleRule("p", "text-base md:text-lg text-black"),

    # Special elements
    "header_text": StyleRule("span", "text-xs text-gray-400 uppercase tracking-wide"),
    "math": StyleRule("span", "font-mono"),

    # Fallback
    "default": StyleRule("p", "text-lg md:text-xl leading-relaxed text-black"),
}

# Image styling
IMAGE_STYLES = {
    "single": "w-full rounded-2xl shadow-lg",
    "multiple": "rounded-xl shadow-md",
    "grid": "grid grid-cols-2 gap-4",
}

# Section type to layout mapping
SECTION_LAYOUTS = {
    "front_cover": {
        "bg_class": "bg-white",
        "container_class": "w-full max-w-5xl",
        "content_class": "p-8 md:p-12",
    },
    "text_only": {
        "bg_class": "bg-[#8F78B6]",
        "container_class": "w-full max-w-5xl px-10 py-10",
        "content_class": "bg-white rounded-[36px] p-10 shadow-[0_18px_30px_-22px_rgba(0,0,0,0.55)]",
    },
    "text_and_single_image": {
        "bg_class": "bg-[#8F78B6]",
        "container_class": "w-full max-w-5xl px-10 py-10",
        "content_class": "bg-white rounded-[36px] p-10 shadow-[0_18px_30px_-22px_rgba(0,0,0,0.55)]",
    },
    "text_and_images": {
        "bg_class": "bg-[#8F78B6]",
        "container_class": "w-full max-w-5xl px-10 py-10",
        "content_class": "bg-white rounded-[36px] p-10 shadow-[0_18px_30px_-22px_rgba(0,0,0,0.55)]",
    },
    "single_image": {
        "bg_class": "bg-[#8F78B6]",
        "container_class": "w-full max-w-5xl px-10 py-10",
        "content_class": "bg-white rounded-[36px] p-10 shadow-[0_18px_30px_-22px_rgba(0,0,0,0.55)]",
    },
    "separator": {
        "bg_class": "bg-[#8F78B6]",
        "container_class": "w-full max-w-5xl px-10 py-10",
        "content_class": "bg-white rounded-[36px] p-10 shadow-[0_18px_30px_-22px_rgba(0,0,0,0.55)]",
    },
    "default": {
        "bg_class": "bg-[#8F78B6]",
        "container_class": "w-full max-w-5xl px-10 py-10",
        "content_class": "bg-white rounded-[36px] p-10 shadow-[0_18px_30px_-22px_rgba(0,0,0,0.55)]",
    },
}


def get_style_for_text_type(text_type: str, style_map: dict[str, StyleRule] | None = None) -> StyleRule:
    """Get the style rule for a text type."""
    if style_map is None:
        style_map = DEFAULT_STYLE_MAP
    return style_map.get(text_type, style_map.get("default", DEFAULT_STYLE_MAP["default"]))


def get_layout_for_section_type(section_type: str) -> dict[str, str]:
    """Get the layout config for a section type."""
    return SECTION_LAYOUTS.get(section_type, SECTION_LAYOUTS["default"])


def generate_content_manifest(
    plate: Plate,
    style_map: dict[str, StyleRule] | None = None,
) -> str:
    """
    Generate a content manifest markdown file with all book content
    and a consistent style map.

    This is used as reference for the LLM during page generation.
    """
    if style_map is None:
        style_map = DEFAULT_STYLE_MAP

    lines = [
        f"# Content Manifest: {plate.title}",
        "",
        "## Style Map (APPLY CONSISTENTLY TO ALL PAGES)",
        "",
        "| Text Type | HTML Element | Tailwind Classes |",
        "|-----------|--------------|------------------|",
    ]

    for text_type, rule in style_map.items():
        lines.append(f"| `{text_type}` | `<{rule.html_element}>` | `{rule.tailwind_classes}` |")

    lines.extend([
        "",
        "## Image Styling",
        "",
        "| Type | Classes |",
        "|------|---------|",
        f"| Single image | `{IMAGE_STYLES['single']}` |",
        f"| Multiple images | `{IMAGE_STYLES['multiple']}` |",
        f"| Image grid container | `{IMAGE_STYLES['grid']}` |",
        "",
        "---",
        "",
    ])

    # Build lookups
    texts_by_id = {t.text_id: t for t in plate.texts}
    images_by_id = {i.image_id: i for i in plate.images}
    groups_by_id = {g.group_id: g for g in plate.groups}

    # Generate section content
    for section in plate.sections:
        lines.append(f"## Section: {section.section_id}")
        lines.append(f"**Type:** `{section.section_type}`")
        if section.page_number:
            lines.append(f"**Page:** {section.page_number}")
        lines.append("")

        # Get layout for this section type
        layout = get_layout_for_section_type(section.section_type)
        lines.append("### Layout")
        lines.append(f"- Background: `{layout['bg_class']}`")
        lines.append(f"- Container: `{layout['container_class']}`")
        lines.append(f"- Content panel: `{layout['content_class']}`")
        lines.append("")

        # Collect texts and images for this section
        section_texts: list[PlateText] = []
        section_images: list[PlateImage] = []
        section_groups: list[PlateGroup] = []

        for part_id in section.part_ids:
            if part_id in texts_by_id:
                section_texts.append(texts_by_id[part_id])
            elif part_id in images_by_id:
                section_images.append(images_by_id[part_id])
            elif part_id in groups_by_id:
                group = groups_by_id[part_id]
                section_groups.append(group)
                # Add group texts
                for text_id in group.text_ids:
                    if text_id in texts_by_id:
                        section_texts.append(texts_by_id[text_id])

        # Output text content with styling
        if section_texts or section_groups:
            lines.append("### Text Content")
            lines.append("")

            # Group texts by their groups if available
            processed_text_ids = set()

            for group in section_groups:
                lines.append(f"#### Group: {group.group_id} (type: `{group.group_type}`)")
                for text_id in group.text_ids:
                    if text_id in texts_by_id:
                        text = texts_by_id[text_id]
                        style = get_style_for_text_type(text.text_type, style_map)
                        lines.append(f"- `{text.text_id}` ({text.text_type})")
                        lines.append(f"  - **Element:** `<{style.html_element}>`")
                        lines.append(f"  - **Classes:** `{style.tailwind_classes}`")
                        lines.append(f"  - **Text:** \"{text.text[:100]}{'...' if len(text.text) > 100 else ''}\"")
                        processed_text_ids.add(text_id)
                lines.append("")

            # Output ungrouped texts
            ungrouped = [t for t in section_texts if t.text_id not in processed_text_ids]
            if ungrouped:
                lines.append("#### Ungrouped Text")
                for text in ungrouped:
                    style = get_style_for_text_type(text.text_type, style_map)
                    lines.append(f"- `{text.text_id}` ({text.text_type})")
                    lines.append(f"  - **Element:** `<{style.html_element}>`")
                    lines.append(f"  - **Classes:** `{style.tailwind_classes}`")
                    lines.append(f"  - **Text:** \"{text.text[:100]}{'...' if len(text.text) > 100 else ''}\"")
                lines.append("")

        # Output images
        if section_images:
            lines.append("### Images")
            image_class = IMAGE_STYLES["single"] if len(section_images) == 1 else IMAGE_STYLES["multiple"]
            for img in section_images:
                lines.append(f"- `{img.image_id}`")
                lines.append(f"  - **Path:** `images/{img.image_id}.jpg`")
                lines.append(f"  - **Classes:** `{image_class}`")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _generate_text_html(
    text: PlateText,
    style_map: dict[str, StyleRule],
) -> str:
    """Generate HTML for a single text element."""
    style = get_style_for_text_type(text.text_type, style_map)
    return f'<{style.html_element} class="{style.tailwind_classes}" data-id="{text.text_id}">{text.text}</{style.html_element}>'


def _generate_group_html(
    group: PlateGroup,
    texts_by_id: dict[str, PlateText],
    style_map: dict[str, StyleRule],
    processed_text_ids: set[str],
) -> str:
    """Generate HTML for a text group."""
    group_html = []
    for text_id in group.text_ids:
        if text_id in texts_by_id:
            text = texts_by_id[text_id]
            element_html = _generate_text_html(text, style_map)
            group_html.append(element_html)
            processed_text_ids.add(text_id)
    if group_html:
        return f'<div class="space-y-4">\n  ' + '\n  '.join(group_html) + '\n</div>'
    return ""


def _generate_image_html(img: PlateImage, class_override: str | None = None) -> str:
    """Generate HTML for an image element."""
    classes = class_override or f'{IMAGE_STYLES["single"]}'
    return f'<img class="{classes}" data-id="{img.image_id}" src="images/{img.image_id}.jpg" alt="" />'


def _collect_content_by_type(
    section: PlateSection,
    texts_by_id: dict[str, PlateText],
    images_by_id: dict[str, PlateImage],
    groups_by_id: dict[str, PlateGroup],
    style_map: dict[str, StyleRule],
) -> tuple[list[str], list[str], set[str]]:
    """
    Collect text and image HTML separately while respecting part_ids order.
    Returns (text_parts, image_parts, processed_text_ids).
    """
    text_parts: list[str] = []
    image_parts: list[str] = []
    processed_text_ids: set[str] = set()

    for part_id in section.part_ids:
        if part_id in groups_by_id:
            group = groups_by_id[part_id]
            html = _generate_group_html(group, texts_by_id, style_map, processed_text_ids)
            if html:
                text_parts.append(html)
        elif part_id in texts_by_id and part_id not in processed_text_ids:
            text = texts_by_id[part_id]
            text_parts.append(_generate_text_html(text, style_map))
            processed_text_ids.add(part_id)
        elif part_id in images_by_id:
            img = images_by_id[part_id]
            image_parts.append(_generate_image_html(img))

    return text_parts, image_parts, processed_text_ids


def _generate_stacked_content(
    section: PlateSection,
    texts_by_id: dict[str, PlateText],
    images_by_id: dict[str, PlateImage],
    groups_by_id: dict[str, PlateGroup],
    style_map: dict[str, StyleRule],
) -> str:
    """Generate stacked (vertical) layout - respects part_ids order."""
    content_parts: list[str] = []
    processed_text_ids: set[str] = set()

    for part_id in section.part_ids:
        if part_id in groups_by_id:
            group = groups_by_id[part_id]
            html = _generate_group_html(group, texts_by_id, style_map, processed_text_ids)
            if html:
                content_parts.append(html)
        elif part_id in texts_by_id and part_id not in processed_text_ids:
            text = texts_by_id[part_id]
            content_parts.append(_generate_text_html(text, style_map))
            processed_text_ids.add(part_id)
        elif part_id in images_by_id:
            img = images_by_id[part_id]
            content_parts.append(_generate_image_html(img, f'{IMAGE_STYLES["single"]} mt-6'))

    return '\n'.join(content_parts)


def _generate_side_by_side_content(
    section: PlateSection,
    texts_by_id: dict[str, PlateText],
    images_by_id: dict[str, PlateImage],
    groups_by_id: dict[str, PlateGroup],
    style_map: dict[str, StyleRule],
    text_first: bool = True,
) -> str:
    """Generate side-by-side layout (text and images in columns)."""
    text_parts, image_parts, _ = _collect_content_by_type(
        section, texts_by_id, images_by_id, groups_by_id, style_map
    )

    text_column = f'<div class="flex-1 space-y-4">\n  ' + '\n  '.join(text_parts) + '\n</div>' if text_parts else ''
    image_column = f'<div class="flex-1 space-y-4">\n  ' + '\n  '.join(
        [_generate_image_html(images_by_id[img_id], f'{IMAGE_STYLES["single"]}')
         for img_id in section.part_ids if img_id in images_by_id]
    ) + '\n</div>' if image_parts else ''

    if text_first:
        return f'<div class="flex flex-col md:flex-row gap-8">\n  {text_column}\n  {image_column}\n</div>'
    else:
        return f'<div class="flex flex-col md:flex-row gap-8">\n  {image_column}\n  {text_column}\n</div>'


def _generate_image_top_content(
    section: PlateSection,
    texts_by_id: dict[str, PlateText],
    images_by_id: dict[str, PlateImage],
    groups_by_id: dict[str, PlateGroup],
    style_map: dict[str, StyleRule],
) -> str:
    """Generate layout with image(s) at top, text below."""
    text_parts, image_parts, _ = _collect_content_by_type(
        section, texts_by_id, images_by_id, groups_by_id, style_map
    )

    # Images at top
    if len(image_parts) == 1:
        images_html = _generate_image_html(
            [images_by_id[pid] for pid in section.part_ids if pid in images_by_id][0],
            f'{IMAGE_STYLES["single"]} mb-6'
        )
    else:
        grid_items = '\n  '.join([
            _generate_image_html(images_by_id[pid], IMAGE_STYLES["multiple"])
            for pid in section.part_ids if pid in images_by_id
        ])
        images_html = f'<div class="{IMAGE_STYLES["grid"]} mb-6">\n  {grid_items}\n</div>'

    # Text below
    text_html = '<div class="space-y-4">\n  ' + '\n  '.join(text_parts) + '\n</div>' if text_parts else ''

    return f'{images_html}\n{text_html}'


def _generate_grid_images_content(
    section: PlateSection,
    texts_by_id: dict[str, PlateText],
    images_by_id: dict[str, PlateImage],
    groups_by_id: dict[str, PlateGroup],
    style_map: dict[str, StyleRule],
) -> str:
    """Generate grid layout for multiple images with text."""
    text_parts, _, _ = _collect_content_by_type(
        section, texts_by_id, images_by_id, groups_by_id, style_map
    )

    # Text first
    text_html = '<div class="space-y-4 mb-6">\n  ' + '\n  '.join(text_parts) + '\n</div>' if text_parts else ''

    # Images in grid
    grid_items = '\n  '.join([
        _generate_image_html(images_by_id[pid], IMAGE_STYLES["multiple"])
        for pid in section.part_ids if pid in images_by_id
    ])
    images_html = f'<div class="{IMAGE_STYLES["grid"]}">\n  {grid_items}\n</div>'

    return f'{text_html}\n{images_html}' if text_html else images_html


def _generate_two_column_text_content(
    section: PlateSection,
    texts_by_id: dict[str, PlateText],
    images_by_id: dict[str, PlateImage],
    groups_by_id: dict[str, PlateGroup],
    style_map: dict[str, StyleRule],
) -> str:
    """Generate two-column text layout."""
    text_parts, image_parts, _ = _collect_content_by_type(
        section, texts_by_id, images_by_id, groups_by_id, style_map
    )

    # Split text into two columns
    mid = len(text_parts) // 2 or 1
    col1 = text_parts[:mid]
    col2 = text_parts[mid:]

    col1_html = '<div class="flex-1 space-y-4">\n  ' + '\n  '.join(col1) + '\n</div>' if col1 else ''
    col2_html = '<div class="flex-1 space-y-4">\n  ' + '\n  '.join(col2) + '\n</div>' if col2 else ''

    text_html = f'<div class="flex flex-col md:flex-row gap-8">\n  {col1_html}\n  {col2_html}\n</div>'

    # Images below if any
    if image_parts:
        images = [images_by_id[pid] for pid in section.part_ids if pid in images_by_id]
        if len(images) == 1:
            images_html = _generate_image_html(images[0], f'{IMAGE_STYLES["single"]} mt-6')
        else:
            grid_items = '\n  '.join([_generate_image_html(img, IMAGE_STYLES["multiple"]) for img in images])
            images_html = f'<div class="{IMAGE_STYLES["grid"]} mt-6">\n  {grid_items}\n</div>'
        return f'{text_html}\n{images_html}'

    return text_html


def generate_section_html(
    section: PlateSection,
    texts: list[PlateText],
    images: list[PlateImage],
    groups: list[PlateGroup],
    style_map: dict[str, StyleRule] | None = None,
) -> str:
    """
    Generate HTML for a single section using the style map.

    This is a deterministic, non-LLM approach that directly applies
    the style map to generate consistent HTML.

    Supports different layouts based on section.layout_hint:
    - "stacked": Default vertical layout
    - "text_left_image_right": Two-column with text left, image right
    - "image_left_text_right": Two-column with image left, text right
    - "image_top": Image at top, text below
    - "two_column_text": Two columns of text
    - "grid_images": Grid layout for multiple images
    """
    if style_map is None:
        style_map = DEFAULT_STYLE_MAP

    layout = get_layout_for_section_type(section.section_type)
    texts_by_id = {t.text_id: t for t in texts}
    images_by_id = {i.image_id: i for i in images}
    groups_by_id = {g.group_id: g for g in groups}

    # Generate content based on layout hint
    layout_hint = getattr(section, 'layout_hint', 'stacked')

    if layout_hint == "text_left_image_right":
        inner_content = _generate_side_by_side_content(
            section, texts_by_id, images_by_id, groups_by_id, style_map, text_first=True
        )
    elif layout_hint == "image_left_text_right":
        inner_content = _generate_side_by_side_content(
            section, texts_by_id, images_by_id, groups_by_id, style_map, text_first=False
        )
    elif layout_hint == "image_top":
        inner_content = _generate_image_top_content(
            section, texts_by_id, images_by_id, groups_by_id, style_map
        )
    elif layout_hint == "grid_images":
        inner_content = _generate_grid_images_content(
            section, texts_by_id, images_by_id, groups_by_id, style_map
        )
    elif layout_hint == "two_column_text":
        inner_content = _generate_two_column_text_content(
            section, texts_by_id, images_by_id, groups_by_id, style_map
        )
    else:  # "stacked" or default
        inner_content = _generate_stacked_content(
            section, texts_by_id, images_by_id, groups_by_id, style_map
        )

    html = f'''<div class="min-h-[calc(100dvh-100px)] flex justify-center items-start {layout["bg_class"]}">
  <section role="article" data-section-type="{section.section_type}" class="relative {layout["container_class"]}">
    <div class="relative {layout["content_class"]}">
{_indent(inner_content, 6)}
    </div>
  </section>
</div>'''

    return html


def _indent(text: str, spaces: int) -> str:
    """Indent each line of text by the specified number of spaces."""
    indent = " " * spaces
    return "\n".join(indent + line if line.strip() else line for line in text.split("\n"))
