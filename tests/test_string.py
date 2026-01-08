"""Tests for string utility functions."""

from adt_press.utils.string import is_speakable_text, page_number_for_section_id


class TestPageNumberForSectionId:
    """Test page number extraction from section IDs."""

    def test_basic_section_id(self):
        """Test extracting page number from standard section ID."""
        assert page_number_for_section_id("sec_p5_s1") == 5

    def test_double_digit_page(self):
        """Test extracting double digit page numbers."""
        assert page_number_for_section_id("sec_p42_s3") == 42

    def test_triple_digit_page(self):
        """Test extracting triple digit page numbers."""
        assert page_number_for_section_id("sec_p123_s1") == 123


class TestIsSpeakableText:
    """Test speakable text validation."""

    def test_empty_string(self):
        """Test that empty string is not speakable."""
        assert is_speakable_text("") is False

    def test_whitespace_only(self):
        """Test that whitespace-only text is not speakable."""
        assert is_speakable_text("   ") is False
        assert is_speakable_text("\n\t") is False

    def test_none_input(self):
        """Test that None input is not speakable."""
        assert is_speakable_text(None) is False  # type: ignore

    def test_punctuation_only_short(self):
        """Test that short punctuation-only text is not speakable."""
        assert is_speakable_text("—") is False
        assert is_speakable_text(".") is False
        assert is_speakable_text(",") is False
        assert is_speakable_text("...") is False

    def test_punctuation_only_long(self):
        """Test that long punctuation-only text is not speakable."""
        assert is_speakable_text("." * 80) is False
        assert is_speakable_text("—" * 50) is False
        assert is_speakable_text(",,,,,,,,,,,,,,,,,,,,") is False

    def test_symbols_only(self):
        """Test that symbol-only text is not speakable."""
        assert is_speakable_text("$$$") is False
        assert is_speakable_text("@#$%") is False
        assert is_speakable_text("***") is False

    def test_number_only(self):
        """Test that numbers are speakable."""
        assert is_speakable_text("1") is True
        assert is_speakable_text("42") is True
        assert is_speakable_text("123") is True

    def test_number_with_punctuation(self):
        """Test that numbers with punctuation are speakable."""
        assert is_speakable_text("1.") is True
        assert is_speakable_text("2)") is True
        assert is_speakable_text("(3)") is True

    def test_letter_only(self):
        """Test that letters are speakable."""
        assert is_speakable_text("a") is True
        assert is_speakable_text("vi") is True
        assert is_speakable_text("i") is True

    def test_mixed_short_text(self):
        """Test that short text with mixed content is speakable."""
        assert is_speakable_text("a)") is True
        assert is_speakable_text("1)") is True
        assert is_speakable_text("(i)") is True

    def test_unicode_letters(self):
        """Test that Unicode letters are recognized as speakable."""
        assert is_speakable_text("ä") is True  # German
        assert is_speakable_text("ñ") is True  # Spanish
        assert is_speakable_text("ß") is True  # German
        assert is_speakable_text("å") is True  # Nordic
        assert is_speakable_text("ō") is True  # Latin extended
        assert is_speakable_text("א") is True  # Hebrew
        assert is_speakable_text("あ") is True  # Japanese Hiragana
        assert is_speakable_text("中") is True  # Chinese
        assert is_speakable_text("අ") is True  # Sinhala
        assert is_speakable_text("த") is True  # Tamil
        assert is_speakable_text("Ω") is True  # Greek

    def test_unicode_numbers(self):
        """Test that Unicode numbers are recognized as speakable."""
        assert is_speakable_text("٣") is True  # Arabic-Indic digit 3
        assert is_speakable_text("५") is True  # Devanagari digit 5
        assert is_speakable_text("二") is True  # Chinese number 2

    def test_long_speakable_text(self):
        """Test that normal long text is speakable."""
        assert is_speakable_text("Hello world") is True
        assert is_speakable_text("This is a test sentence.") is True
        assert is_speakable_text("Page 42 of the document") is True

    def test_whitespace_trimming(self):
        """Test that surrounding whitespace is properly handled."""
        assert is_speakable_text("  a  ") is True
        assert is_speakable_text("  .  ") is False
        assert is_speakable_text("\n1\n") is True

    def test_custom_min_length(self):
        """Test custom min_length parameter (note: this parameter no longer affects logic)."""
        # With the fix, min_length doesn't change behavior - we always check for letters/numbers
        assert is_speakable_text(".", min_length=1) is False
        assert is_speakable_text("a", min_length=5) is True

    def test_real_world_examples(self):
        """Test real-world examples from document processing."""
        # List markers
        assert is_speakable_text("1.") is True
        assert is_speakable_text("a)") is True
        assert is_speakable_text("i.") is True

        # Page numbers
        assert is_speakable_text("42") is True
        assert is_speakable_text("Page 10") is True

        # Punctuation-only (should be skipped)
        assert is_speakable_text("—") is False
        assert is_speakable_text("...") is False
        assert is_speakable_text("." * 80) is False  # The failing case from error

        # Mixed content
        assert is_speakable_text("Chapter 1") is True
        assert is_speakable_text("Figure 2.3") is True
