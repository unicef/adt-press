import unicodedata


def page_number_for_section_id(section_id: str) -> int:
    """Generate a human-readable title for a given section ID."""
    parts = section_id.split("_")
    return int(parts[1][1:])


def is_speakable_text(text: str, min_length: int = 3) -> bool:
    """
    Check if text contains speakable content suitable for TTS generation.

    Texts that are too short and contain only punctuation/symbols often cause
    TTS APIs (especially Azure) to return empty responses.

    Args:
        text: The text to validate
        min_length: Minimum length threshold for short text validation (default: 3)

    Returns:
        True if text is suitable for TTS, False if it should be skipped

    Examples:
        >>> is_speakable_text("1.")
        True  # Contains number
        >>> is_speakable_text("vi")
        True  # Contains letters
        >>> is_speakable_text("—")
        False  # Only punctuation
        >>> is_speakable_text(".")
        False  # Only punctuation
        >>> is_speakable_text("Hello world")
        True  # Normal text (length > min_length)
    """
    if not text or not text.strip():
        return False

    stripped = text.strip()

    # Text longer than min_length is generally safe to speak
    if len(stripped) >= min_length:
        return True

    # For short texts, check if they contain any letters or numbers
    # Unicode categories: L* = letters (La, Ll, Lm, Lo, Lt, Lu)
    #                     N* = numbers (Nd, Nl, No)
    has_speakable = any(unicodedata.category(c).startswith(("L", "N")) for c in stripped)

    return has_speakable
