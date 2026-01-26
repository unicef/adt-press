# mypy: ignore-errors
"""
Fixed template extraction for consistent HTML generation.

This module analyzes sample pages from the book and generates a fixed set
of HTML templates - one per section type. These templates are then used
for all pages of that type, ensuring visual consistency throughout the book.
"""

import base64
import os
from typing import Optional

import instructor
import structlog
from openai import AsyncOpenAI
from pydantic import BaseModel, Field, field_validator

from adt_press.models.plate import Plate

log = structlog.get_logger(__name__)


class TemplateSlot(BaseModel):
    """A slot in a template that will be filled with content."""

    name: str = Field(description="Slot name, e.g., 'heading', 'body_paragraphs', 'image'")
    slot_type: str = Field(description="Type: 'text_single', 'text_multiple', 'image', 'image_multiple'")
    description: str = Field(description="What content goes in this slot")
    html_wrapper: str = Field(
        description="Complete HTML with ALL Tailwind classes. Example: '<h1 class=\"text-4xl font-bold text-black\" data-id=\"{id}\">{text}</h1>'"
    )
    tailwind_classes: str = Field(
        default="",
        description="The exact Tailwind classes for this slot, e.g., 'text-4xl font-bold text-black leading-tight'"
    )
    custom_css: str = Field(
        default="",
        description="Any custom CSS needed (as inline style or CSS class), e.g., 'font-size: 2.5rem; line-height: 1.2;'"
    )


class PageTemplate(BaseModel):
    """A fixed HTML template for a specific section type."""

    name: str = Field(description="Template name, e.g., 'chapter_opener', 'text_page'")
    section_types: list[str] = Field(description="Section types this template handles")
    description: str = Field(description="When to use this template")
    slots: list[TemplateSlot] = Field(description="The slots in this template")
    html_template: str = Field(description="Complete HTML template with {slot_name} placeholders")
    css_classes: dict[str, str] = Field(
        default_factory=dict,
        description="Key CSS classes used, e.g., {'heading': 'text-4xl font-bold text-amber-700'}",
    )

    @field_validator("css_classes", mode="before")
    @classmethod
    def coerce_css_classes(cls, v):
        """Handle both string and dict inputs for css_classes."""
        if isinstance(v, str):
            # If LLM returns a plain string, wrap it in a dict
            return {"classes": v} if v.strip() else {}
        if v is None:
            return {}
        return v


class BookTemplateSet(BaseModel):
    """Complete set of templates for a book."""

    book_title: str
    design_style: str = Field(description="Overall design style description")
    color_palette: dict[str, str] = Field(
        default_factory=dict,
        description="Color tokens: {'primary': '#A48DC0', 'heading': '#2A2A2A', ...}",
    )
    templates: list[PageTemplate] = Field(description="All page templates for this book")

    @field_validator("color_palette", mode="before")
    @classmethod
    def coerce_color_palette(cls, v):
        """Handle unexpected inputs for color_palette."""
        if isinstance(v, str):
            return {"primary": v} if v.strip() else {}
        if v is None:
            return {}
        return v


async def extract_book_templates(
    plate: Plate,
    model: str,
    output_dir: str,
) -> BookTemplateSet:
    """
    Analyze sample pages and generate fixed templates for each section type.

    This runs once per book and generates templates that will be used
    for ALL pages, ensuring consistency.
    """
    client = instructor.from_openai(AsyncOpenAI())

    # Get sample pages - one for each section type
    section_type_samples: dict[str, list[str]] = {}
    for section in plate.sections:
        st = section.section_type
        if st not in section_type_samples:
            section_type_samples[st] = []
        if len(section_type_samples[st]) < 2 and section.page_image_path:
            section_type_samples[st].append(section.page_image_path)

    # Build the image content for the prompt
    image_content = []
    section_type_list = []

    for section_type, paths in section_type_samples.items():
        section_type_list.append(section_type)
        for path in paths:
            if os.path.exists(path):
                with open(path, "rb") as f:
                    img_data = base64.standard_b64encode(f.read()).decode("utf-8")
                image_content.append({
                    "type": "text",
                    "text": f"\n--- Section Type: {section_type} ---"
                })
                image_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_data}",
                        "detail": "high"
                    }
                })

    # Limit images to avoid token limits
    max_images = 12
    image_count = sum(1 for c in image_content if c.get("type") == "image_url")
    if image_count > max_images:
        # Take first max_images images
        new_content = []
        img_seen = 0
        for c in image_content:
            if c.get("type") == "image_url":
                if img_seen < max_images:
                    new_content.append(c)
                    img_seen += 1
            else:
                new_content.append(c)
        image_content = new_content

    system_prompt = """You are a design system architect. Analyze the sample pages from this book and create a FIXED set of HTML templates with PRECISE styling for every element.

## YOUR TASK
1. Identify the distinct page layout patterns in this book
2. Create ONE HTML template per pattern
3. **CRITICAL: Capture EXACT typography, colors, and spacing for EVERY slot**
4. Templates must ensure visual consistency across ALL pages

## CRITICAL REQUIREMENTS

### 1. SLOT STYLING IS MANDATORY
For EVERY slot, you MUST provide:
- `tailwind_classes`: The EXACT Tailwind classes (e.g., "text-4xl md:text-5xl font-extrabold text-black leading-tight")
- `html_wrapper`: Complete HTML with ALL classes included
- `custom_css`: Any additional CSS if Tailwind isn't sufficient

### 2. TYPOGRAPHY REQUIREMENTS
Analyze the images and extract:
- **Headings**: Font size (use text-3xl to text-6xl), weight (font-bold/extrabold), color, line height
- **Body text**: Font size (text-lg to text-2xl), line height (leading-relaxed/snug), color
- **Captions**: Smaller text, often italic or muted colors

### 3. IMAGE STYLING REQUIREMENTS
- Border radius (rounded-lg, rounded-2xl, rounded-3xl)
- Shadows (shadow-md, shadow-lg, shadow-xl)
- Width constraints (w-full, max-w-md, etc.)
- Margins/spacing (mt-6, mb-4, etc.)

### 4. COLOR PALETTE
Extract EXACT hex colors from the images:
- Background colors (e.g., bg-[#8F78B6])
- Text colors (e.g., text-[#2A2A2A])
- Accent colors for badges, borders

## SLOT TYPES AND EXPECTED STYLING

### text_single (headings)
```
tailwind_classes: "text-4xl md:text-5xl font-extrabold text-black leading-tight"
html_wrapper: "<h1 class=\"text-4xl md:text-5xl font-extrabold text-black leading-tight\" data-id=\"{id}\">{text}</h1>"
```

### text_multiple (body paragraphs)
```
tailwind_classes: "text-xl md:text-2xl leading-relaxed text-black"
html_wrapper: "<div class=\"space-y-4\"><p class=\"text-xl md:text-2xl leading-relaxed text-black\" data-id=\"{id}\">{text}</p></div>"
```

### image (single image)
```
tailwind_classes: "w-full rounded-2xl shadow-lg mt-6"
html_wrapper: "<img class=\"w-full rounded-2xl shadow-lg mt-6\" data-id=\"{id}\" src=\"images/{id}.jpg\" alt=\"\" />"
```

### image_multiple (multiple images)
```
tailwind_classes: "grid grid-cols-2 gap-4"
html_wrapper: "<div class=\"grid grid-cols-2 gap-4\"><img class=\"rounded-xl shadow-md\" data-id=\"{id}\" src=\"images/{id}.jpg\" alt=\"\" /></div>"
```

## HTML TEMPLATE FORMAT
The html_template should include INLINE styling in every element:
```html
<div class="min-h-[calc(100dvh-100px)] flex justify-center items-start bg-[#8F78B6]">
  <section role="article" data-section-type="{section_type}" class="relative w-full max-w-5xl px-10 py-10">
    <div class="relative bg-white rounded-[36px] p-10 shadow-[0_18px_30px_-22px_rgba(0,0,0,0.55)]">
      <h1 class="text-4xl md:text-5xl font-extrabold text-black leading-tight" data-id="{heading_id}">{slot_heading}</h1>
      <div class="mt-6 space-y-4 text-xl md:text-2xl leading-relaxed text-black">
        {slot_body}
      </div>
      <img class="mt-6 w-full rounded-2xl shadow-lg" data-id="{image_id}" src="images/{slot_image}.jpg" alt="" />
    </div>
  </section>
</div>
```

## STANDARD SECTION TYPES TO HANDLE
- front_cover, back_cover
- separator (chapter openers) - ALL MUST LOOK IDENTICAL
- text_only
- text_and_images, text_and_single_image
- single_image
- credits, table_of_contents
- activity_* (various activity types)

**REMEMBER**: The LLM filling these templates will ONLY replace slot placeholders. ALL styling must be baked into the template itself."""

    user_content = [
        {
            "type": "text",
            "text": f"""Analyze these sample pages from "{plate.title}" and create fixed HTML templates.

Section types found in this book: {', '.join(section_type_list)}

Sample pages by section type:"""
        },
        *image_content,
        {
            "type": "text",
            "text": """

Based on these samples, create a BookTemplateSet with:
1. The book's color palette (extract exact colors from the images)
2. A template for EACH section type pattern
3. Ensure separator/chapter pages ALL use one template

Remember: The goal is CONSISTENCY. Every page of the same type must look identical."""
        }
    ]

    log.info(
        "extracting_book_templates",
        book_title=plate.title,
        section_types=section_type_list,
        num_images=sum(1 for c in image_content if c.get("type") == "image_url"),
    )

    response: BookTemplateSet = await client.chat.completions.create(
        model=model,
        response_model=BookTemplateSet,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        max_completion_tokens=16000,
        timeout=300,
    )

    # Save templates to file
    output_path = os.path.join(output_dir, "book_templates.md")
    save_templates_markdown(response, output_path)

    log.info(
        "book_templates_extracted",
        num_templates=len(response.templates),
        template_names=[t.name for t in response.templates],
    )

    return response


def save_templates_markdown(templates: BookTemplateSet, output_path: str) -> None:
    """Save templates to a markdown file for review."""
    lines = [
        f"# {templates.book_title} - Fixed Page Templates\n",
        f"**Design Style:** {templates.design_style}\n",
        "## Color Palette\n",
    ]

    for name, color in templates.color_palette.items():
        lines.append(f"- **{name}**: `{color}`")
    lines.append("")

    lines.append("---\n")
    lines.append("# Templates\n")

    for template in templates.templates:
        lines.append(f"## {template.name}")
        lines.append(f"_{template.description}_\n")
        lines.append(f"**Section Types:** {', '.join(template.section_types)}\n")

        lines.append("### Slots")
        for slot in template.slots:
            lines.append(f"- `{{{slot.name}}}` ({slot.slot_type}): {slot.description}")
            if slot.tailwind_classes:
                lines.append(f"  - **Tailwind**: `{slot.tailwind_classes}`")
            if slot.custom_css:
                lines.append(f"  - **CSS**: `{slot.custom_css}`")
            lines.append(f"  - **HTML**: `{slot.html_wrapper}`")
        lines.append("")

        lines.append("### HTML Template")
        lines.append("```html")
        lines.append(template.html_template)
        lines.append("```")
        lines.append("")

        lines.append("### CSS Classes")
        for element, classes in template.css_classes.items():
            lines.append(f"- **{element}**: `{classes}`")
        lines.append("\n---\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def get_template_for_section(
    templates: BookTemplateSet,
    section_type: str,
) -> Optional[PageTemplate]:
    """Get the template that handles a given section type."""
    for template in templates.templates:
        if section_type in template.section_types:
            return template

    # Fallback: try to find a generic template
    for template in templates.templates:
        if "text_only" in template.section_types or "content" in template.name.lower():
            return template

    # Last resort: return first template
    return templates.templates[0] if templates.templates else None


def templates_to_markdown(templates: BookTemplateSet) -> str:
    """Convert templates to markdown string for use in prompts."""
    lines = [
        f"# {templates.book_title} - Fixed Page Templates\n",
        f"**Design Style:** {templates.design_style}\n",
        "## Color Palette (USE THESE EXACT COLORS)\n",
    ]

    for name, color in templates.color_palette.items():
        lines.append(f"- **{name}**: `{color}` → Tailwind: `text-[{color}]` or `bg-[{color}]`")
    lines.append("")

    lines.append("---\n")

    for template in templates.templates:
        lines.append(f"## Template: {template.name}")
        lines.append(f"**For section types:** {', '.join(template.section_types)}\n")
        lines.append(f"_{template.description}_\n")

        lines.append("### Slots to Fill (USE THESE EXACT STYLES)")
        for slot in template.slots:
            lines.append(f"- `{{{slot.name}}}` ({slot.slot_type})")
            lines.append(f"  - {slot.description}")
            if slot.tailwind_classes:
                lines.append(f"  - **REQUIRED Tailwind classes**: `{slot.tailwind_classes}`")
            if slot.custom_css:
                lines.append(f"  - **Additional CSS**: `{slot.custom_css}`")
            lines.append(f"  - **HTML pattern**: `{slot.html_wrapper}`")
        lines.append("")

        lines.append("### Complete HTML Template")
        lines.append("```html")
        lines.append(template.html_template)
        lines.append("```")
        lines.append("\n---\n")

    return "\n".join(lines)
