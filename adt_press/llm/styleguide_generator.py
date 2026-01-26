"""
Dynamic styleguide generator using LLM.

This module implements the second part of the two-pass generation approach:
Generate a book-specific styleguide based on analysis results.
"""

import structlog

from adt_press.llm.book_analysis import BookAnalysis, generate_analysis_summary

log = structlog.get_logger(__name__)

# Base styleguide template that the LLM will enhance
BASE_STYLEGUIDE = """# ADT Style Guide - STRICT RULES

## CRITICAL TEXT RULES
- ❌ **NO TEXT DUPLICATION** - Each data-id must appear exactly ONCE
- ❌ **NO TEXT MODIFICATION** - Use exact text provided, do not rephrase

## TEXT TYPE STYLING (USE THESE EXACT CLASSES)

### Headings and Titles
| Text Type | HTML Element | CSS Classes |
|-----------|--------------|-------------|
| `section_heading` | `<h1>` | `text-5xl font-bold mb-4 text-amber-700` |
| `book_title` | `<h1>` | `text-5xl font-bold mb-4 text-amber-700` |
| `activity_title` | `<h1>` | `text-5xl font-bold mb-4 text-amber-700` |
| `chapter_title` | `<h1>` | `text-4xl md:text-5xl font-bold text-gray-900 leading-tight` |

### Chapter/Separator Page Elements
| Text Type | HTML Element | CSS Classes |
|-----------|--------------|-------------|
| `chapter_number` | `<p>` | `text-xl font-semibold text-gray-800 tracking-wide` |
| `chapter_label` | `<p>` | `text-xl font-semibold text-gray-800 tracking-wide` |
| Standalone numbers (1, 2, 3...) | `<p>` | `text-4xl font-bold text-amber-700` |

### Body Text
| Text Type | HTML Element | CSS Classes |
|-----------|--------------|-------------|
| `section_text` | `<p>` | `text-lg text-gray-900 leading-relaxed mb-4` |
| `instruction_text` | `<p>` | `text-xl text-gray-700 mb-8` |
| `activity_option` | varies | `text-lg text-gray-900` |

### Captions and Metadata
| Text Type | HTML Element | CSS Classes |
|-----------|--------------|-------------|
| `image_caption` | `<p>` | `text-sm text-gray-600 text-center mt-2` |
| `image_associated_text` | `<p>` | `text-sm text-gray-600 mt-2` |
| `footer_text` | `<p>` | `text-sm text-gray-500` |
| `page_number` | `<p>` | `text-sm text-gray-400` |

## FORBIDDEN ELEMENTS (NEVER USE THESE)
- ❌ NO gradient backgrounds (`bg-gradient-*`)
- ❌ NO blur effects (`blur-*`)
- ❌ NO decorative shapes or circles
- ❌ NO `absolute` positioned decorative elements
- ❌ NO decorative dividers or separators
- ❌ NO `aria-hidden="true"` decorative elements
- ❌ NO colored container backgrounds (keep `bg-white`)
- ❌ NO shadow effects except `shadow-sm` on images

## EXACT CONTAINER STRUCTURE (USE THIS EXACTLY)
Every page MUST use this exact structure with no modifications:

```html
<div class="flex justify-center items-start min-h-[calc(100dvh-100px)]">
  <div class="container mx-auto max-w-5xl bg-white rounded-lg lg:px-24 md:px-12 sm:px-6 pt-12 pb-12" id="content">
    <section data-section-type="[TYPE]" role="article">
      <!-- Content here -->
    </section>
  </div>
</div>
```

## IMAGE STRUCTURE (EXACT FORMAT)
Images must use this exact structure:

```html
<img
  src="images/xxx.jpg"
  data-id="img_xxx"
  alt="Description"
  class="w-full max-w-md rounded-lg shadow-sm"
/>
```

## RULES SUMMARY
1. Use the exact classes specified in TEXT TYPE STYLING tables above
2. NO decorative elements of any kind
3. Container is ALWAYS `bg-white`
4. Match text type to the correct styling from the tables
5. Images use `rounded-lg shadow-sm` only
6. Keep layouts simple: single column or simple 2-column flex
"""


def generate_section_type_templates(analysis: BookAnalysis) -> str:
    """
    Generate layout guidance for each section type based on analysis.

    These templates provide layout structure guidance while the TEXT TYPE STYLING
    table in the base styleguide dictates the actual element styling.
    """
    templates = []

    for section_type, type_analysis in analysis.section_types.items():
        if type_analysis.count == 0:
            continue

        # Determine layout based on patterns
        has_images = type_analysis.avg_image_count > 0.5
        is_text_heavy = type_analysis.avg_text_count > 5

        template_lines = [f"## {section_type.upper()} SECTION"]
        template_lines.append(f"Count in book: {type_analysis.count}")
        template_lines.append("")

        # Show what text types are commonly found
        if type_analysis.common_text_types:
            sorted_types = sorted(
                type_analysis.common_text_types.items(),
                key=lambda x: -x[1]
            )[:5]
            template_lines.append("**Common text types found:**")
            for text_type, count in sorted_types:
                template_lines.append(f"- `{text_type}` ({count} occurrences)")
            template_lines.append("")

        # Layout guidance based on section type
        if section_type in ["separator", "front_cover", "back_cover", "inside_cover"]:
            template_lines.append("**Layout:** Centered content")
            template_lines.append("- Center all content using `text-center` on a wrapper div")
            template_lines.append("- Use `flex items-baseline gap-4` for chapter label + number")
            template_lines.append("- Style chapter titles prominently")
            template_lines.append("")
            template_lines.append("**Typical structure:**")
            template_lines.append("```html")
            template_lines.append('<div class="flex items-baseline gap-4 mb-6">')
            template_lines.append('  <p class="text-xl font-semibold text-gray-800 tracking-wide" data-id="...">CHAPTER</p>')
            template_lines.append('  <p class="text-4xl font-bold text-amber-700" data-id="...">3</p>')
            template_lines.append("</div>")
            template_lines.append('<p class="text-4xl md:text-5xl font-bold text-gray-900 leading-tight" data-id="...">Chapter Title</p>')
            template_lines.append("```")

        elif section_type == "text_only" or (not has_images and is_text_heavy):
            template_lines.append("**Layout:** Single column text flow")
            template_lines.append("- Stack paragraphs vertically")
            template_lines.append("- Use appropriate styling from TEXT TYPE STYLING table")
            template_lines.append("")
            template_lines.append("**Typical structure:**")
            template_lines.append("```html")
            template_lines.append('<h1 class="..." data-id="...">Heading (if section_heading type)</h1>')
            template_lines.append('<p class="text-lg text-gray-900 leading-relaxed mb-4" data-id="...">Paragraph</p>')
            template_lines.append("```")

        elif section_type == "text_and_single_image":
            template_lines.append("**Layout:** Two column (text + image)")
            template_lines.append("- Use `flex flex-col md:flex-row gap-6 items-start`")
            template_lines.append("- Text in `flex-1` div, image in `md:w-1/3` div")
            template_lines.append("")
            template_lines.append("**Typical structure:**")
            template_lines.append("```html")
            template_lines.append('<div class="flex flex-col md:flex-row gap-6 items-start">')
            template_lines.append('  <div class="flex-1">')
            template_lines.append('    <p class="text-lg text-gray-900 leading-relaxed mb-4" data-id="...">Text</p>')
            template_lines.append("  </div>")
            template_lines.append('  <div class="md:w-1/3">')
            template_lines.append('    <img class="w-full rounded-lg shadow-sm" data-id="..." />')
            template_lines.append("  </div>")
            template_lines.append("</div>")
            template_lines.append("```")

        elif section_type == "text_and_images" or has_images:
            template_lines.append("**Layout:** Text with images")
            template_lines.append("- Use `flex flex-col md:flex-row gap-6` for mixed layouts")
            template_lines.append("- Use `grid grid-cols-2 gap-4` for multiple images")
            template_lines.append("")
            template_lines.append("**Typical structure:**")
            template_lines.append("```html")
            template_lines.append('<p class="text-lg text-gray-900 leading-relaxed mb-4" data-id="...">Text</p>')
            template_lines.append('<div class="flex flex-col md:flex-row gap-6">')
            template_lines.append('  <img class="w-full md:w-1/2 rounded-lg shadow-sm" data-id="..." />')
            template_lines.append('  <img class="w-full md:w-1/2 rounded-lg shadow-sm" data-id="..." />')
            template_lines.append("</div>")
            template_lines.append("```")

        elif section_type.startswith("activity_"):
            template_lines.append("**Layout:** Activity with instruction")
            template_lines.append("- Title using `activity_title` styling")
            template_lines.append("- Instructions using `instruction_text` styling")
            template_lines.append("- Activity content below")
            template_lines.append("")
            template_lines.append("**Typical structure:**")
            template_lines.append("```html")
            template_lines.append('<h1 class="text-5xl font-bold mb-4 text-amber-700" data-id="...">Title</h1>')
            template_lines.append('<p class="text-xl text-gray-700 mb-8" data-id="...">Instructions</p>')
            template_lines.append("<!-- Activity-specific content -->")
            template_lines.append("```")

        else:
            template_lines.append("**Layout:** Standard content")
            template_lines.append("- Use appropriate styling from TEXT TYPE STYLING table")
            template_lines.append("- Keep layout simple and clean")

        template_lines.append("")
        templates.append("\n".join(template_lines))

    return "\n".join(templates)


def generate_dynamic_styleguide(analysis: BookAnalysis, base_styleguide: str = "") -> str:
    """
    Generate a book-specific styleguide based on analysis results.

    This creates a deterministic styleguide with exact templates for each
    section type found in the book, ensuring consistent output.
    """
    # Start with base styleguide or default
    if not base_styleguide:
        base_styleguide = BASE_STYLEGUIDE

    # Generate section-specific templates
    section_templates = generate_section_type_templates(analysis)

    # Combine into final styleguide
    styleguide = f"""{base_styleguide}

# BOOK-SPECIFIC SECTION GUIDANCE

The following guidance is generated based on analysis of this specific book.
Use these layouts combined with the TEXT TYPE STYLING rules above.

{section_templates}

## IMPORTANT: STYLING PRIORITY

When generating HTML for a section:
1. **TEXT TYPE STYLING takes priority** - Always use the correct CSS classes from the TEXT TYPE STYLING table based on the text's type
2. **Use the layout guidance** from the section templates above for structure
3. Match each text element to its text type and apply the corresponding styling
4. Keep layouts consistent within each section type
5. NO decorative elements - focus on clean, consistent styling
"""

    log.info(
        "dynamic_styleguide_generated",
        section_types=list(analysis.section_types.keys()),
        styleguide_length=len(styleguide),
    )

    return styleguide
