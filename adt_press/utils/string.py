def page_number_for_section_id(section_id: str) -> int:
    """Generate a human-readable title for a given section ID."""
    parts = section_id.split("_")
    return int(parts[1][1:])
