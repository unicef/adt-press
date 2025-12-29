import unittest

from adt_press.utils.string import is_speakable_text, page_number_for_section_id


class TestIsSpeakableText(unittest.TestCase):
    """Test is_speakable_text function for TTS validation."""

    def test_empty_string(self):
        """Test that empty strings are not speakable."""
        self.assertFalse(is_speakable_text(""))
        self.assertFalse(is_speakable_text("   "))
        self.assertFalse(is_speakable_text("\t\n"))

    def test_none_value(self):
        """Test that None is not speakable."""
        self.assertFalse(is_speakable_text(None))

    def test_punctuation_only_short(self):
        """Test that short punctuation-only text is not speakable."""
        self.assertFalse(is_speakable_text("—"))
        self.assertFalse(is_speakable_text("."))
        self.assertFalse(is_speakable_text(","))
        self.assertFalse(is_speakable_text(".."))
        self.assertFalse(is_speakable_text("—-"))
        self.assertFalse(is_speakable_text("()"))
        self.assertFalse(is_speakable_text("[]"))
        self.assertFalse(is_speakable_text("{}"))

    def test_symbols_only_short(self):
        """Test that short symbol-only text is not speakable."""
        self.assertFalse(is_speakable_text("$"))
        self.assertFalse(is_speakable_text("@"))
        self.assertFalse(is_speakable_text("#"))
        self.assertFalse(is_speakable_text("*"))

    def test_numbers_short(self):
        """Test that short text with numbers is speakable."""
        self.assertTrue(is_speakable_text("1"))
        self.assertTrue(is_speakable_text("1."))
        self.assertTrue(is_speakable_text("2."))
        self.assertTrue(is_speakable_text("10"))
        self.assertTrue(is_speakable_text("99"))

    def test_letters_short(self):
        """Test that short text with letters is speakable."""
        self.assertTrue(is_speakable_text("a"))
        self.assertTrue(is_speakable_text("A"))
        self.assertTrue(is_speakable_text("vi"))
        self.assertTrue(is_speakable_text("i"))
        self.assertTrue(is_speakable_text("II"))

    def test_mixed_short(self):
        """Test that short mixed text with letters/numbers is speakable."""
        self.assertTrue(is_speakable_text("a)"))
        self.assertTrue(is_speakable_text("1)"))
        self.assertTrue(is_speakable_text("A."))
        self.assertTrue(is_speakable_text("(i)"))
        self.assertTrue(is_speakable_text("(1)"))

    def test_unicode_letters_short(self):
        """Test that short Unicode letter text is speakable."""
        # Sinhala
        self.assertTrue(is_speakable_text("අ"))
        self.assertTrue(is_speakable_text("එ"))
        # Arabic
        self.assertTrue(is_speakable_text("ع"))
        # Chinese
        self.assertTrue(is_speakable_text("中"))
        # Greek
        self.assertTrue(is_speakable_text("α"))
        self.assertTrue(is_speakable_text("β"))

    def test_unicode_numbers_short(self):
        """Test that short Unicode number text is speakable."""
        # Arabic-Indic digits
        self.assertTrue(is_speakable_text("١"))
        self.assertTrue(is_speakable_text("٢"))
        # Chinese numbers
        self.assertTrue(is_speakable_text("一"))

    def test_long_text_always_speakable(self):
        """Test that text longer than min_length is always speakable."""
        # Even if it's all punctuation, long text is considered speakable
        # (though it may fail at TTS API level)
        self.assertTrue(is_speakable_text("..."))
        self.assertTrue(is_speakable_text("----"))
        self.assertTrue(is_speakable_text("Hello"))
        self.assertTrue(is_speakable_text("Hello, world!"))
        self.assertTrue(is_speakable_text("This is a test."))

    def test_whitespace_handling(self):
        """Test that whitespace is properly stripped."""
        self.assertTrue(is_speakable_text("  1  "))
        self.assertTrue(is_speakable_text("\tvi\n"))
        self.assertFalse(is_speakable_text("  .  "))
        self.assertFalse(is_speakable_text("\t—\n"))

    def test_custom_min_length(self):
        """Test custom min_length parameter."""
        # With min_length=1, single characters that are letters/numbers are always speakable
        self.assertTrue(is_speakable_text("a", min_length=1))
        self.assertTrue(is_speakable_text("1", min_length=1))

        # With min_length=5, shorter text goes through validation
        self.assertTrue(is_speakable_text("test", min_length=5))  # Has letters
        self.assertFalse(is_speakable_text("...", min_length=5))  # Only punctuation

        # With min_length=10, medium text is automatically speakable
        self.assertTrue(is_speakable_text(".....", min_length=1))  # > min_length

    def test_real_world_examples(self):
        """Test real-world examples from text extraction."""
        # List markers - should be speakable
        self.assertTrue(is_speakable_text("1."))
        self.assertTrue(is_speakable_text("2."))
        self.assertTrue(is_speakable_text("a)"))
        self.assertTrue(is_speakable_text("i)"))

        # Page numbers - should be speakable
        self.assertTrue(is_speakable_text("vi"))
        self.assertTrue(is_speakable_text("vii"))
        self.assertTrue(is_speakable_text("12"))

        # Pure punctuation - should not be speakable
        self.assertFalse(is_speakable_text("—"))
        self.assertFalse(is_speakable_text("–"))
        self.assertFalse(is_speakable_text("-"))

        # Normal text - should be speakable
        self.assertTrue(is_speakable_text("Hello"))
        self.assertTrue(is_speakable_text("Test"))

        # Sinhala text - should be speakable
        self.assertTrue(is_speakable_text("බුද්ධ"))
        self.assertTrue(is_speakable_text("ධර්මය"))


class TestPageNumberForSectionId(unittest.TestCase):
    """Test page_number_for_section_id function."""

    def test_basic_section_id(self):
        """Test extracting page number from section ID."""
        self.assertEqual(page_number_for_section_id("section_p1"), 1)
        self.assertEqual(page_number_for_section_id("section_p2"), 2)
        self.assertEqual(page_number_for_section_id("section_p10"), 10)
        self.assertEqual(page_number_for_section_id("section_p99"), 99)

    def test_section_id_with_suffix(self):
        """Test section IDs with additional suffixes."""
        self.assertEqual(page_number_for_section_id("section_p5_intro"), 5)
        self.assertEqual(page_number_for_section_id("section_p12_conclusion"), 12)

    def test_large_page_numbers(self):
        """Test large page numbers."""
        self.assertEqual(page_number_for_section_id("section_p100"), 100)
        self.assertEqual(page_number_for_section_id("section_p999"), 999)


if __name__ == "__main__":
    unittest.main()
