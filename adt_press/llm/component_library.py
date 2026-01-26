"""
Component library generator.

This module generates a markdown file containing the complete design system
and component library extracted from the book's visual design.
"""

import structlog

from adt_press.llm.design_extraction import BookDesignSystem, ComponentPattern

log = structlog.get_logger(__name__)


def generate_component_library_markdown(design_system: BookDesignSystem) -> str:
    """
    Generate a complete component library as a markdown document.

    This document will be used by the LLM to generate consistent HTML
    by selecting and populating components.
    """
    sections = []

    # Header
    sections.append(f"# {design_system.book_title} - Design System & Component Library\n")
    sections.append(f"**Design Style:** {design_system.design_style}\n")
    sections.append("---\n")

    # Design Principles
    sections.append("## Design Principles\n")
    for principle in design_system.design_principles:
        sections.append(f"- {principle}")
    sections.append("")

    # Color Palette
    sections.append("## Color Palette\n")
    sections.append("Use these EXACT colors for consistency:\n")
    sections.append("| Token | Hex | Tailwind Class | Usage |")
    sections.append("|-------|-----|----------------|-------|")
    sections.append(
        f"| Primary | `{design_system.colors.primary}` | "
        f"`text-[{design_system.colors.primary}]` / `bg-[{design_system.colors.primary}]` | Brand color, accents |"
    )
    sections.append(
        f"| Secondary | `{design_system.colors.secondary}` | "
        f"`text-[{design_system.colors.secondary}]` / `bg-[{design_system.colors.secondary}]` | Secondary elements |"
    )
    sections.append(
        f"| Accent | `{design_system.colors.accent}` | "
        f"`text-[{design_system.colors.accent}]` / `bg-[{design_system.colors.accent}]` | Highlights, CTAs |"
    )
    sections.append(
        f"| Heading | `{design_system.colors.heading_color}` | "
        f"`text-[{design_system.colors.heading_color}]` | All headings |"
    )
    sections.append(
        f"| Text Primary | `{design_system.colors.text_primary}` | "
        f"`text-[{design_system.colors.text_primary}]` | Body text |"
    )
    sections.append(
        f"| Text Secondary | `{design_system.colors.text_secondary}` | "
        f"`text-[{design_system.colors.text_secondary}]` | Captions, metadata |"
    )
    sections.append(
        f"| Background | `{design_system.colors.background}` | "
        f"`bg-[{design_system.colors.background}]` | Page background |"
    )
    sections.append("")

    # Typography
    sections.append("## Typography\n")
    sections.append(f"- **Headings:** {design_system.typography.heading_style}")
    if design_system.typography.uses_serif:
        sections.append("  - Uses serif font for headings")
    if design_system.typography.uses_all_caps_headings:
        sections.append("  - Headings are in ALL CAPS")
    sections.append(f"- **Body Text:** {design_system.typography.body_style}")
    sections.append(f"- **Captions:** {design_system.typography.caption_style}")
    sections.append("")

    # Layout Patterns
    sections.append("## Layout Patterns\n")
    for layout in design_system.layouts:
        sections.append(f"### {layout.name}")
        sections.append(f"_{layout.description}_\n")
        sections.append(f"- Content Width: `{layout.content_width}`")
        sections.append(f"- Text Alignment: `{layout.text_alignment}`")
        sections.append(f"- Image Position: `{layout.image_position}`")
        if layout.has_sidebar:
            sections.append("- Has sidebar")
        sections.append("")

    # Components - The main section
    sections.append("---\n")
    sections.append("# COMPONENT LIBRARY\n")
    sections.append("**IMPORTANT:** You MUST use these components exactly as defined.")
    sections.append("Select the appropriate component and fill in the slots with content.\n")

    # Group components by category
    components_by_category: dict[str, list[ComponentPattern]] = {}
    for component in design_system.components:
        category = component.category
        if category not in components_by_category:
            components_by_category[category] = []
        components_by_category[category].append(component)

    for category, components in components_by_category.items():
        sections.append(f"## {category.title()} Components\n")

        for component in components:
            sections.append(f"### `{component.name}`")
            sections.append(f"_{component.description}_\n")
            sections.append(f"**When to use:** {component.when_to_use}\n")
            sections.append("**Slots:**")
            for slot in component.slots:
                sections.append(f"- `{{{slot}}}`")
            sections.append("")
            sections.append("**HTML Template:**")
            sections.append("```html")
            sections.append(component.html_structure)
            sections.append("```")
            sections.append("")

    # Consistency Notes
    sections.append("---\n")
    sections.append("## Consistency Guidelines\n")
    sections.append(design_system.consistency_notes)
    sections.append("")

    # Usage Instructions
    sections.append("## How to Use This Library\n")
    sections.append("1. **Identify the content type** - What kind of content are you rendering?")
    sections.append("2. **Select the appropriate component** - Match content to component")
    sections.append("3. **Fill in the slots** - Replace `{slot_name}` with actual content")
    sections.append("4. **Use exact colors** - Reference the Color Palette above")
    sections.append("5. **Maintain structure** - Do not modify the component HTML structure")
    sections.append("")
    sections.append("### Content Slot Rules")
    sections.append("- Each `data-id` must appear exactly ONCE")
    sections.append("- Do not add text that wasn't provided")
    sections.append("- Do not duplicate content across slots")
    sections.append("- Preserve all `data-id` attributes on elements")

    return "\n".join(sections)


def generate_component_selection_guide(design_system: BookDesignSystem) -> str:
    """
    Generate a quick-reference guide for component selection.

    This is a condensed version to help the LLM quickly select components.
    """
    lines = ["# Component Selection Guide\n"]
    lines.append("Match your section type to the appropriate component:\n")

    # Create a mapping table
    lines.append("| Section Type | Recommended Component |")
    lines.append("|--------------|----------------------|")

    # Map section types to components based on component descriptions
    for component in design_system.components:
        when = component.when_to_use.lower()
        section_type = "content"  # default

        if "cover" in when:
            section_type = "front_cover, back_cover"
        elif "chapter" in when or "separator" in when:
            section_type = "separator"
        elif "heading" in when or "title" in when:
            section_type = "section with heading"
        elif "image" in when and "text" in when:
            section_type = "text_and_images, text_and_single_image"
        elif "image" in when:
            section_type = "image sections"
        elif "text" in when:
            section_type = "text_only"
        elif "activity" in when:
            section_type = "activity_*"

        lines.append(f"| {section_type} | `{component.name}` |")

    lines.append("")
    return "\n".join(lines)


def save_component_library(
    design_system: BookDesignSystem,
    output_path: str,
) -> str:
    """
    Save the component library to a markdown file.

    Returns the path to the saved file.
    """
    markdown = generate_component_library_markdown(design_system)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    log.info(
        "component_library_saved",
        path=output_path,
        num_components=len(design_system.components),
        length=len(markdown),
    )

    return output_path
