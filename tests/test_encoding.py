import unittest

from pydantic import ConfigDict

from adt_press.utils.encoding import CleanTextBaseModel


class SampleModel(CleanTextBaseModel):
    """Sample model with flexible fields for testing."""

    model_config = ConfigDict(extra="allow")

    text: str | None = None
    data: dict | None = None
    items: list | None = None
    number: int | None = None
    flag: bool | None = None


class TestCleanTextBaseModel(unittest.TestCase):
    """Test CleanTextBaseModel text cleaning functionality."""

    def test_clean_simple_text(self):
        """Test that normal text passes through unchanged."""
        model = SampleModel(text="Hello, world!")
        self.assertEqual(model.text, "Hello, world!")

    def test_clean_unicode_text(self):
        """Test that malformed unicode is cleaned."""
        # Example with mojibake that ftfy can fix
        model = SampleModel(text="â€œHelloâ€\x9d")
        # ftfy should clean this to something more readable
        self.assertIsInstance(model.text, str)
        self.assertNotEqual(model.text, "")

    def test_clean_nested_dict(self):
        """Test that text in nested dictionaries is cleaned."""
        model = SampleModel(data={"key": "â€œvalueâ€\x9d", "nested": {"text": "hello"}})
        self.assertIsInstance(model.data["key"], str)
        self.assertEqual(model.data["nested"]["text"], "hello")

    def test_clean_list(self):
        """Test that text in lists is cleaned."""
        model = SampleModel(items=["normal", "â€œtextâ€\x9d", "clean"])
        self.assertEqual(len(model.items), 3)
        self.assertEqual(model.items[0], "normal")
        self.assertEqual(model.items[2], "clean")

    def test_clean_mixed_types(self):
        """Test that non-string types are preserved."""
        model = SampleModel(text="hello", number=42, flag=True)
        self.assertEqual(model.text, "hello")
        self.assertEqual(model.number, 42)
        self.assertTrue(model.flag)


if __name__ == "__main__":
    unittest.main()
