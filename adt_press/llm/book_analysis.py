"""
Book analysis module for detecting patterns and generating consistent styleguides.

This module implements the first pass of the two-pass generation approach:
1. Analyze all sections to identify patterns (chapter pages, section layouts, etc.)
2. Generate a book-specific styleguide with exact component templates
"""

from collections import defaultdict
from dataclasses import dataclass, field

import structlog

from adt_press.models.plate import Plate, PlateGroup, PlateImage, PlateSection, PlateText

log = structlog.get_logger(__name__)


@dataclass
class SectionPattern:
    """Represents the pattern of a single section."""

    section_id: str
    section_type: str
    text_count: int
    image_count: int
    group_count: int
    text_types: list[str]
    group_types: list[str]
    has_heading: bool
    has_instruction: bool
    part_sequence: list[str]  # e.g., ["text", "image", "text"]


@dataclass
class SectionTypeAnalysis:
    """Analysis results for a specific section type."""

    section_type: str
    count: int
    patterns: list[SectionPattern]
    avg_text_count: float
    avg_image_count: float
    common_text_types: dict[str, int]
    common_group_types: dict[str, int]
    common_part_sequences: dict[str, int]
    has_heading_ratio: float
    has_instruction_ratio: float


@dataclass
class BookAnalysis:
    """Complete analysis of a book's structure and patterns."""

    total_sections: int
    section_types: dict[str, SectionTypeAnalysis]
    all_text_types: set[str]
    all_group_types: set[str]
    dominant_patterns: dict[str, str]  # section_type -> dominant pattern description


def analyze_section(
    section: PlateSection,
    groups_by_id: dict[str, PlateGroup],
    images_by_id: dict[str, PlateImage],
    texts_by_id: dict[str, PlateText],
) -> SectionPattern:
    """Analyze a single section to extract its pattern."""
    text_types: list[str] = []
    group_types: list[str] = []
    part_sequence: list[str] = []
    text_count = 0
    image_count = 0
    group_count = 0

    for part_id in section.part_ids:
        if part_id.startswith("grp_"):
            group = groups_by_id.get(part_id)
            if group:
                group_count += 1
                group_types.append(group.group_type)
                part_sequence.append("text_group")

                for text_id in group.text_ids:
                    text = texts_by_id.get(text_id)
                    if text:
                        text_count += 1
                        text_types.append(text.text_type)

        elif part_id.startswith("img_"):
            image = images_by_id.get(part_id)
            if image:
                image_count += 1
                part_sequence.append("image")

    has_heading = any(t in ["section_heading", "book_title", "activity_title", "chapter_title"] for t in text_types)
    has_instruction = any(t in ["instruction_text", "activity_number"] for t in text_types)

    return SectionPattern(
        section_id=section.section_id,
        section_type=section.section_type,
        text_count=text_count,
        image_count=image_count,
        group_count=group_count,
        text_types=text_types,
        group_types=group_types,
        has_heading=has_heading,
        has_instruction=has_instruction,
        part_sequence=part_sequence,
    )


def analyze_section_type(section_type: str, patterns: list[SectionPattern]) -> SectionTypeAnalysis:
    """Analyze all sections of a specific type to find common patterns."""
    if not patterns:
        return SectionTypeAnalysis(
            section_type=section_type,
            count=0,
            patterns=[],
            avg_text_count=0,
            avg_image_count=0,
            common_text_types={},
            common_group_types={},
            common_part_sequences={},
            has_heading_ratio=0,
            has_instruction_ratio=0,
        )

    count = len(patterns)
    avg_text_count = sum(p.text_count for p in patterns) / count
    avg_image_count = sum(p.image_count for p in patterns) / count

    # Count occurrences of text types
    text_type_counts: dict[str, int] = defaultdict(int)
    for p in patterns:
        for t in p.text_types:
            text_type_counts[t] += 1

    # Count occurrences of group types
    group_type_counts: dict[str, int] = defaultdict(int)
    for p in patterns:
        for g in p.group_types:
            group_type_counts[g] += 1

    # Count occurrences of part sequences (as tuple strings)
    sequence_counts: dict[str, int] = defaultdict(int)
    for p in patterns:
        seq_key = ",".join(p.part_sequence)
        sequence_counts[seq_key] += 1

    has_heading_count = sum(1 for p in patterns if p.has_heading)
    has_instruction_count = sum(1 for p in patterns if p.has_instruction)

    return SectionTypeAnalysis(
        section_type=section_type,
        count=count,
        patterns=patterns,
        avg_text_count=avg_text_count,
        avg_image_count=avg_image_count,
        common_text_types=dict(text_type_counts),
        common_group_types=dict(group_type_counts),
        common_part_sequences=dict(sequence_counts),
        has_heading_ratio=has_heading_count / count,
        has_instruction_ratio=has_instruction_count / count,
    )


def get_dominant_pattern(analysis: SectionTypeAnalysis) -> str:
    """Describe the dominant pattern for a section type."""
    if analysis.count == 0:
        return "empty"

    parts = []

    # Heading presence
    if analysis.has_heading_ratio > 0.5:
        parts.append("with heading")

    # Text density
    if analysis.avg_text_count > 5:
        parts.append("text-heavy")
    elif analysis.avg_text_count > 2:
        parts.append("moderate text")
    elif analysis.avg_text_count > 0:
        parts.append("minimal text")

    # Image presence
    if analysis.avg_image_count > 2:
        parts.append("multiple images")
    elif analysis.avg_image_count > 0.5:
        parts.append("single image")
    else:
        parts.append("no images")

    # Most common sequence
    if analysis.common_part_sequences:
        most_common_seq = max(analysis.common_part_sequences.items(), key=lambda x: x[1])
        if most_common_seq[0]:
            seq_parts = most_common_seq[0].split(",")
            if seq_parts == ["text_group", "image"]:
                parts.append("text-left layout")
            elif seq_parts == ["image", "text_group"]:
                parts.append("image-left layout")
            elif all(p == "text_group" for p in seq_parts):
                parts.append("text-only layout")
            elif all(p == "image" for p in seq_parts):
                parts.append("image-only layout")

    return ", ".join(parts) if parts else "standard"


def analyze_book(plate: Plate) -> BookAnalysis:
    """
    Analyze a complete book to identify patterns across all sections.

    Returns a BookAnalysis object containing:
    - Per-section-type analysis with patterns
    - Dominant patterns for each type
    - Global statistics
    """
    groups_by_id = {grp.group_id: grp for grp in plate.groups}
    images_by_id = {img.image_id: img for img in plate.images}
    texts_by_id = {txt.text_id: txt for txt in plate.texts}

    # Analyze each section
    patterns_by_type: dict[str, list[SectionPattern]] = defaultdict(list)
    all_text_types: set[str] = set()
    all_group_types: set[str] = set()

    for section in plate.sections:
        pattern = analyze_section(section, groups_by_id, images_by_id, texts_by_id)
        patterns_by_type[section.section_type].append(pattern)
        all_text_types.update(pattern.text_types)
        all_group_types.update(pattern.group_types)

    # Analyze each section type
    section_type_analyses: dict[str, SectionTypeAnalysis] = {}
    dominant_patterns: dict[str, str] = {}

    for section_type, patterns in patterns_by_type.items():
        analysis = analyze_section_type(section_type, patterns)
        section_type_analyses[section_type] = analysis
        dominant_patterns[section_type] = get_dominant_pattern(analysis)

    log.info(
        "book_analysis_complete",
        total_sections=len(plate.sections),
        section_types=list(section_type_analyses.keys()),
        dominant_patterns=dominant_patterns,
    )

    return BookAnalysis(
        total_sections=len(plate.sections),
        section_types=section_type_analyses,
        all_text_types=all_text_types,
        all_group_types=all_group_types,
        dominant_patterns=dominant_patterns,
    )


def generate_analysis_summary(analysis: BookAnalysis) -> str:
    """
    Generate a human-readable summary of the book analysis.

    This summary can be included in the LLM prompt for styleguide generation.
    """
    lines = ["# Book Structure Analysis", ""]

    lines.append(f"**Total Sections:** {analysis.total_sections}")
    lines.append("")

    lines.append("## Section Types Found")
    lines.append("")

    for section_type, type_analysis in sorted(analysis.section_types.items(), key=lambda x: -x[1].count):
        lines.append(f"### {section_type} ({type_analysis.count} sections)")
        lines.append(f"- **Pattern:** {analysis.dominant_patterns[section_type]}")
        lines.append(f"- **Avg text elements:** {type_analysis.avg_text_count:.1f}")
        lines.append(f"- **Avg images:** {type_analysis.avg_image_count:.1f}")
        lines.append(f"- **Has heading:** {type_analysis.has_heading_ratio * 100:.0f}%")

        if type_analysis.common_text_types:
            top_types = sorted(type_analysis.common_text_types.items(), key=lambda x: -x[1])[:5]
            lines.append(f"- **Common text types:** {', '.join(t[0] for t in top_types)}")

        if type_analysis.common_part_sequences:
            top_seqs = sorted(type_analysis.common_part_sequences.items(), key=lambda x: -x[1])[:3]
            lines.append(f"- **Common layouts:** {'; '.join(s[0] for s in top_seqs if s[0])}")

        lines.append("")

    lines.append("## Text Types Used")
    lines.append(", ".join(sorted(analysis.all_text_types)))
    lines.append("")

    return "\n".join(lines)
