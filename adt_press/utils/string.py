import unicodedata


def page_number_for_section_id(section_id: str) -> int:
    """Generate a human-readable title for a given section ID."""
    parts = section_id.split("_")
    return int(parts[1][1:])


def is_speakable_text(text: str, min_length: int = 3) -> bool:
    """
    Check if text contains speakable content suitable for TTS generation.

    Texts that contain only punctuation/symbols often cause TTS APIs
    (especially Azure) to return empty responses, regardless of length.

    Args:
        text: The text to validate
        min_length: Minimum length threshold for considering text "long enough" (default: 3)

    Returns:
        True if text contains letters or numbers (speakable content), False otherwise

    Examples:
        >>> is_speakable_text("1.")
        True  # Contains number
        >>> is_speakable_text("vi")
        True  # Contains letters
        >>> is_speakable_text("—")
        False  # Only punctuation
        >>> is_speakable_text(".")
        False  # Only punctuation
        >>> is_speakable_text("................................................................................")
        False  # Only punctuation, even if long
        >>> is_speakable_text("Hello world")
        True  # Contains letters
        >>> is_speakable_text("Page 42")
        True  # Contains letters and numbers
    """
    if not text or not text.strip():
        return False

    stripped = text.strip()

    # Check if text contains any letters or numbers, regardless of length
    # Unicode categories: L* = letters (La, Ll, Lm, Lo, Lt, Lu)
    #                     N* = numbers (Nd, Nl, No)
    has_speakable = any(unicodedata.category(c).startswith(("L", "N")) for c in stripped)

    return has_speakable
