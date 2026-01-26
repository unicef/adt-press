"""
Post-generation consistency checker.

This module implements a second pass that reviews generated HTML pages
and ensures consistent styling across pages of the same section type.
"""

import re
from collections import defaultdict
from dataclasses import dataclass

import structlog
from banks import Prompt
from pydantic import BaseModel

from adt_press.llm import get_instructor_client
from adt_press.models.web import WebPage
from adt_press.utils.file import cached_read_text_file

log = structlog.get_logger(__name__)


class ConsistencyFixResponse(BaseModel):
    """Response from consistency fix LLM call."""

    html: str
    changes_made: list[str]


@dataclass
class StylePattern:
    """Extracted style pattern from an HTML page."""

    section_type: str
    heading_classes: list[str]
    paragraph_classes: list[str]
    container_classes: list[str]
    layout_structure: str  # e.g., "centered", "two-column", "single-column"
    uses_flex: bool
    uses_grid: bool
    is_centered: bool
    raw_html: str


def extract_style_pattern(page: WebPage) -> StylePattern:
    """Extract the style pattern from a web page's HTML."""
    html = page.content

    # Extract heading classes
    heading_pattern = r'<h[1-6][^>]*class="([^"]*)"'
    heading_matches = re.findall(heading_pattern, html)
    heading_classes = list(set(heading_matches))

    # Extract paragraph classes
    p_pattern = r'<p[^>]*class="([^"]*)"'
    p_matches = re.findall(p_pattern, html)
    paragraph_classes = list(set(p_matches))

    # Extract container/div classes (first few significant ones)
    div_pattern = r'<div[^>]*class="([^"]*)"'
    div_matches = re.findall(div_pattern, html)
    container_classes = list(set(div_matches))[:5]

    # Determine layout structure
    is_centered = "text-center" in html or "justify-center" in html
    uses_flex = "flex" in html
    uses_grid = "grid" in html

    if is_centered and not uses_flex:
        layout_structure = "centered"
    elif "flex-row" in html or "md:flex-row" in html:
        layout_structure = "two-column"
    elif uses_grid:
        layout_structure = "grid"
    else:
        layout_structure = "single-column"

    return StylePattern(
        section_type=page.render_strategy,
        heading_classes=heading_classes,
        paragraph_classes=paragraph_classes,
        container_classes=container_classes,
        layout_structure=layout_structure,
        uses_flex=uses_flex,
        uses_grid=uses_grid,
        is_centered=is_centered,
        raw_html=html,
    )


def compare_patterns(reference: StylePattern, candidate: StylePattern) -> list[str]:
    """Compare two style patterns and return list of inconsistencies."""
    inconsistencies = []

    # Check heading consistency
    if set(reference.heading_classes) != set(candidate.heading_classes):
        ref_classes = ", ".join(reference.heading_classes) or "none"
        cand_classes = ", ".join(candidate.heading_classes) or "none"
        inconsistencies.append(
            f"Heading classes differ: reference uses [{ref_classes}], "
            f"this page uses [{cand_classes}]"
        )

    # Check layout structure
    if reference.layout_structure != candidate.layout_structure:
        inconsistencies.append(
            f"Layout differs: reference is '{reference.layout_structure}', "
            f"this page is '{candidate.layout_structure}'"
        )

    # Check centering consistency
    if reference.is_centered != candidate.is_centered:
        ref_centered = "centered" if reference.is_centered else "not centered"
        cand_centered = "centered" if candidate.is_centered else "not centered"
        inconsistencies.append(
            f"Centering differs: reference is {ref_centered}, "
            f"this page is {cand_centered}"
        )

    return inconsistencies


def group_pages_by_section_type(pages: list[WebPage]) -> dict[str, list[WebPage]]:
    """Group web pages by their section type for consistency checking."""
    # We need to extract section type from the HTML since WebPage doesn't store it directly
    grouped: dict[str, list[WebPage]] = defaultdict(list)

    for page in pages:
        # Extract section type from data-section-type attribute
        match = re.search(r'data-section-type="([^"]*)"', page.content)
        if match:
            section_type = match.group(1)
            grouped[section_type].append(page)
        else:
            grouped["unknown"].append(page)

    return dict(grouped)


async def fix_page_consistency(
    page: WebPage,
    reference_page: WebPage,
    inconsistencies: list[str],
    model: str,
) -> WebPage:
    """Use LLM to fix a page's HTML to match the reference style."""
    template_content = cached_read_text_file("prompts/consistency_fix.jinja2")
    prompt = Prompt(template_content)

    context = {
        "reference_html": reference_page.content,
        "page_html": page.content,
        "inconsistencies": inconsistencies,
    }

    messages = [m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)]

    client = get_instructor_client()

    try:
        response = await client.chat.completions.create(
            model=model,
            response_model=ConsistencyFixResponse,
            messages=messages,
            max_completion_tokens=4000,
            temperature=0.1,
        )

        fixed_html = response.html

        log.info(
            "consistency_fix_applied",
            section_id=page.section_id,
            changes=response.changes_made,
        )

    except Exception as e:
        log.warning(
            "consistency_fix_failed",
            section_id=page.section_id,
            error=str(e),
        )
        return page

    # Create new page with fixed content
    return WebPage(
        section_id=page.section_id,
        text_id=page.text_id,
        text_ids=page.text_ids,
        image_ids=page.image_ids,
        generated_texts=page.generated_texts,
        content=fixed_html,
        reasoning=f"Fixed for consistency: {'; '.join(inconsistencies)}",
        render_strategy=page.render_strategy,
        activity_answers=page.activity_answers,
        activity_reasoning=page.activity_reasoning,
        formatted_texts=page.formatted_texts,
    )


async def run_consistency_pass(
    pages: list[WebPage],
    model: str,
) -> list[WebPage]:
    """
    Run a consistency pass over all generated pages.

    For each section type, the first page becomes the reference style,
    and subsequent pages are adjusted to match.
    """
    # Group pages by section type
    grouped = group_pages_by_section_type(pages)

    log.info(
        "consistency_pass_started",
        section_types=list(grouped.keys()),
        total_pages=len(pages),
    )

    # Track which pages need fixing
    pages_to_fix: list[tuple[WebPage, WebPage, list[str]]] = []

    for section_type, section_pages in grouped.items():
        if len(section_pages) < 2:
            # Only one page of this type, nothing to compare
            continue

        # First page is the reference
        reference_page = section_pages[0]
        reference_pattern = extract_style_pattern(reference_page)

        log.info(
            "consistency_reference_set",
            section_type=section_type,
            reference_section_id=reference_page.section_id,
            layout=reference_pattern.layout_structure,
            heading_classes=reference_pattern.heading_classes,
        )

        # Compare subsequent pages
        for page in section_pages[1:]:
            candidate_pattern = extract_style_pattern(page)
            inconsistencies = compare_patterns(
                reference_pattern, candidate_pattern
            )

            if inconsistencies:
                log.info(
                    "consistency_issue_found",
                    section_id=page.section_id,
                    section_type=section_type,
                    inconsistencies=inconsistencies,
                )
                pages_to_fix.append((page, reference_page, inconsistencies))

    if not pages_to_fix:
        log.info("consistency_pass_complete", pages_fixed=0)
        return pages

    # Fix inconsistent pages
    log.info("fixing_inconsistent_pages", count=len(pages_to_fix))

    fixed_pages_map: dict[str, WebPage] = {}
    for page, reference, inconsistencies in pages_to_fix:
        fixed_page = await fix_page_consistency(
            page, reference, inconsistencies, model
        )
        fixed_pages_map[page.section_id] = fixed_page

    # Rebuild pages list with fixed pages
    result_pages = []
    for page in pages:
        if page.section_id in fixed_pages_map:
            result_pages.append(fixed_pages_map[page.section_id])
        else:
            result_pages.append(page)

    log.info("consistency_pass_complete", pages_fixed=len(fixed_pages_map))

    return result_pages
