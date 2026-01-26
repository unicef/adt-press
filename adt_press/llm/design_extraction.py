"""
Visual design extraction from PDF pages.

This module uses vision models to analyze PDF page images and extract
design patterns including colors, typography, layouts, and components.
"""

import base64
from pathlib import Path

import structlog
from pydantic import BaseModel, Field

from adt_press.llm import get_instructor_client
from adt_press.models.plate import Plate
from adt_press.utils.file import cached_read_text_file

log = structlog.get_logger(__name__)


class ColorPalette(BaseModel):
    """Extracted color palette from the design."""

    primary: str = Field(description="Primary brand color (hex)")
    secondary: str = Field(description="Secondary color (hex)")
    accent: str = Field(description="Accent/highlight color (hex)")
    text_primary: str = Field(description="Main text color (hex)")
    text_secondary: str = Field(description="Secondary text color (hex)")
    background: str = Field(description="Background color (hex)")
    heading_color: str = Field(description="Heading text color (hex)")


class TypographyPattern(BaseModel):
    """Typography patterns extracted from the design."""

    heading_style: str = Field(description="Description of heading style (bold, light, etc.)")
    body_style: str = Field(description="Description of body text style")
    caption_style: str = Field(description="Description of caption/small text style")
    uses_serif: bool = Field(description="Whether headings use serif fonts")
    uses_all_caps_headings: bool = Field(description="Whether headings are in all caps")


class LayoutPattern(BaseModel):
    """Layout pattern extracted from a page."""

    name: str = Field(description="Name for this layout pattern")
    description: str = Field(description="Description of the layout")
    content_width: str = Field(description="Content width: narrow, medium, wide, full")
    text_alignment: str = Field(description="Text alignment: left, center, justified")
    has_sidebar: bool = Field(description="Whether layout has sidebar")
    image_position: str = Field(description="Common image position: none, left, right, top, bottom, inline")


class ComponentPattern(BaseModel):
    """A reusable component pattern extracted from the design."""

    name: str = Field(description="Component name (e.g., 'chapter-header', 'text-image-right')")
    category: str = Field(description="Category: header, content, image-layout, callout, navigation")
    description: str = Field(description="What this component is used for")
    html_structure: str = Field(description="Suggested HTML structure with Tailwind classes")
    slots: list[str] = Field(description="Content slots in this component (e.g., 'title', 'body', 'image')")
    when_to_use: str = Field(description="When to use this component")


class PageDesignAnalysis(BaseModel):
    """Design analysis for a single page."""

    page_number: int
    layout_type: str = Field(description="Layout type: cover, chapter-start, content, activity")
    components_found: list[str] = Field(description="Component types found on this page")
    notable_design_elements: list[str] = Field(description="Notable design elements or patterns")


class BookDesignSystem(BaseModel):
    """Complete design system extracted from the book."""

    book_title: str
    design_style: str = Field(description="Overall design style: modern, classic, playful, academic, etc.")
    colors: ColorPalette
    typography: TypographyPattern
    layouts: list[LayoutPattern]
    components: list[ComponentPattern]
    design_principles: list[str] = Field(description="Key design principles observed")
    consistency_notes: str = Field(description="Notes on maintaining consistency")


async def analyze_page_design(
    image_path: str,
    page_number: int,
    model: str,
) -> PageDesignAnalysis:
    """Analyze a single page's design using vision."""
    # Read and encode the image
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # Determine image type
    suffix = Path(image_path).suffix.lower()
    media_type = "image/jpeg" if suffix in [".jpg", ".jpeg"] else "image/png"

    client = get_instructor_client()

    response = await client.chat.completions.create(
        model=model,
        response_model=PageDesignAnalysis,
        messages=[
            {
                "role": "system",
                "content": """You are a professional book designer analyzing page layouts.
Identify the design patterns, components, and layout structures used on this page.
Focus on reusable patterns that appear across multiple pages.""",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Analyze the design of this page (page {page_number}). "
                        "Identify the layout type, components used, and notable design elements.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{image_data}"},
                    },
                ],
            },
        ],
        max_completion_tokens=1000,
        temperature=0.1,
    )

    return response


async def extract_design_system(
    plate: Plate,
    sample_pages: list[str],
    model: str,
) -> BookDesignSystem:
    """
    Extract a complete design system from sample pages.

    Args:
        plate: The plate containing book metadata
        sample_pages: List of image paths for sample pages to analyze
        model: Vision model to use for analysis
    """
    # Encode all sample images (limit to 4 to reduce token usage)
    encoded_images = []
    for path in sample_pages[:4]:  # Limit to 4 pages to stay within token limits
        with open(path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        suffix = Path(path).suffix.lower()
        media_type = "image/jpeg" if suffix in [".jpg", ".jpeg"] else "image/png"
        encoded_images.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{media_type};base64,{image_data}"},
            }
        )

    client = get_instructor_client()

    # Build message content with all images
    content = [
        {
            "type": "text",
            "text": f"""Analyze these pages from "{plate.title}" and extract a complete design system.

I need you to identify:
1. **Color Palette**: Extract the exact colors used (primary, secondary, accent, text colors)
2. **Typography**: Heading styles, body text, captions
3. **Layout Patterns**: Different page layouts used (cover, chapter start, content pages, etc.)
4. **Reusable Components**: Identify distinct components like:
   - Headers (chapter headers, section headers)
   - Content blocks (text-only, text-with-image layouts)
   - Image layouts (single image, image grid, image with caption)
   - Callout boxes, sidebars, or special elements
   - Activity or interactive elements

For each component, provide:
- A descriptive name
- HTML structure using Tailwind CSS
- Content slots (where dynamic content goes)
- When to use this component

Focus on patterns that repeat across pages - these are the reusable components.""",
        },
        *encoded_images,
    ]

    response = await client.chat.completions.create(
        model=model,
        response_model=BookDesignSystem,
        messages=[
            {
                "role": "system",
                "content": """You are an expert book designer and front-end developer.
Your task is to extract a design system from book pages that can be used to generate
consistent HTML/Tailwind CSS components.

Focus on:
- Identifying reusable patterns
- Extracting exact colors (provide hex codes)
- Creating practical HTML components with Tailwind classes
- Ensuring components can be combined consistently""",
            },
            {"role": "user", "content": content},
        ],
        max_completion_tokens=16000,
        temperature=0.2,
    )

    log.info(
        "design_system_extracted",
        book_title=plate.title,
        num_components=len(response.components),
        num_layouts=len(response.layouts),
        design_style=response.design_style,
    )

    return response


def get_sample_pages_for_analysis(plate: Plate, max_pages: int = 10) -> list[str]:
    """
    Select diverse sample pages for design analysis.

    Tries to include: cover, chapter starts, different content types.
    """
    sample_paths = []
    seen_types = set()

    # Group sections by type to get variety
    sections_by_type: dict[str, list] = {}
    for section in plate.sections:
        section_type = section.section_type
        if section_type not in sections_by_type:
            sections_by_type[section_type] = []
        sections_by_type[section_type].append(section)

    # Take one of each section type first
    for section_type, sections in sections_by_type.items():
        if len(sample_paths) >= max_pages:
            break
        section = sections[0]
        if section.page_image_path:
            sample_paths.append(section.page_image_path)
            seen_types.add(section_type)

    # Fill remaining slots with variety
    for section in plate.sections:
        if len(sample_paths) >= max_pages:
            break
        if section.page_image_path and section.page_image_path not in sample_paths:
            sample_paths.append(section.page_image_path)

    log.info(
        "sample_pages_selected",
        count=len(sample_paths),
        section_types=list(seen_types),
    )

    return sample_paths
