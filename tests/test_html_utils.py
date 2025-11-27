"""Tests for HTML utility functions - focused on key functions."""

from bs4 import BeautifulSoup

from adt_press.models.plate import PlateImage, PlateText
from adt_press.utils.html import (
    basename,
    format_html,
    replace_images,
    replace_texts,
    sanitize_generated_html,
)


class TestReplaceImages:
    """Test replace_images function."""

    def test_replaces_image_src_and_alt(self):
        """Test that image src and alt are replaced."""
        html = '<img data-id="img_1" src="old.png" />'
        replacements = {"img_1": PlateImage(image_id="img_1", image_path="new.png", caption_id="txt_1")}
        texts = {"txt_1": PlateText(text_id="txt_1", text_type="paragraph", text="New caption")}

        result = replace_images(html, replacements, texts)

        assert 'src="new.png"' in result
        assert 'alt="New caption"' in result

    def test_preserves_unmatched_images(self):
        """Test that images without matching data-id are preserved."""
        html = '<img data-id="img_2" src="unchanged.png" />'
        replacements = {}
        texts = {}

        result = replace_images(html, replacements, texts)

        assert 'src="unchanged.png"' in result

    def test_handles_missing_caption_text(self):
        """Test handling when caption text doesn't exist."""
        html = '<img data-id="img_1" src="old.png" />'
        replacements = {"img_1": PlateImage(image_id="img_1", image_path="new.png", caption_id="txt_999")}
        texts = {}

        result = replace_images(html, replacements, texts)

        # Should still replace image path
        assert 'src="new.png"' in result


class TestReplaceTexts:
    """Test replace_texts function."""

    def test_replaces_text_in_multiple_tag_types(self):
        """Test that text content is replaced in h1, h2, h3, p, span."""
        html = """
        <h1 data-id="txt_1">Old Title</h1>
        <h2 data-id="txt_2">Old Subtitle</h2>
        <p data-id="txt_3">Old paragraph</p>
        <span data-id="txt_4">Old span</span>
        """
        replacements = {
            "txt_1": PlateText(text_id="txt_1", text_type="heading", text="New Title"),
            "txt_2": PlateText(text_id="txt_2", text_type="heading", text="New Subtitle"),
            "txt_3": PlateText(text_id="txt_3", text_type="paragraph", text="New paragraph"),
            "txt_4": PlateText(text_id="txt_4", text_type="span", text="New span"),
        }

        result = replace_texts(html, replacements)

        assert "New Title" in result
        assert "New Subtitle" in result
        assert "New paragraph" in result
        assert "New span" in result
        assert "Old Title" not in result
        assert "Old paragraph" not in result

    def test_preserves_unmatched_elements(self):
        """Test that elements without data-id in replacements are unchanged."""
        html = '<p data-id="txt_999">Unchanged</p>'
        replacements = {}

        result = replace_texts(html, replacements)

        assert "Unchanged" in result


class TestSanitizeGeneratedHtml:
    """Test sanitize_generated_html function."""

    def test_removes_outer_html_body_tags(self):
        """Test that outer <html> and <body> wrappers are removed."""
        html = "<html><body><div>Content</div></body></html>"

        result = sanitize_generated_html(html)

        assert "<html>" not in result
        assert "<body>" not in result
        assert "<div>Content</div>" in result

    def test_removes_nested_body_tags(self):
        """Test that nested body tags within content are unwrapped."""
        html = "<body><body><div>Nested content</div></body></body>"

        result = sanitize_generated_html(html)

        # All body tags should be removed
        assert result.count("<body>") == 0
        assert "<div>Nested content</div>" in result

    def test_removes_interface_and_nav_containers(self):
        """Test that shell interface elements are removed."""
        html = """
        <div id="interface-container">Interface stuff</div>
        <div id="nav-container">Navigation stuff</div>
        <div>Actual content</div>
        """

        result = sanitize_generated_html(html)

        assert "interface-container" not in result
        assert "nav-container" not in result
        assert "Interface stuff" not in result
        assert "Navigation stuff" not in result
        assert "<div>Actual content</div>" in result

    def test_preserves_html_comments(self):
        """Test that HTML comments are preserved in output."""
        html = "<!-- Important comment --><div>Content</div>"

        result = sanitize_generated_html(html)

        assert "<!-- Important comment -->" in result or "<!--Important comment-->" in result
        assert "<div>Content</div>" in result

    def test_adds_feedback_to_sorting_activity(self):
        """Test that feedback div is added to sorting activities."""
        html = '<section data-section-type="activity_sorting"><div>Sort these items</div></section>'

        result = sanitize_generated_html(html)

        soup = BeautifulSoup(result, "html.parser")
        feedback = soup.find(id="feedback")

        assert feedback is not None
        assert feedback.get("aria-live") == "polite"

    def test_preserves_existing_feedback_in_section(self):
        """Test that existing feedback element in section is not duplicated."""
        html = '<section data-section-type="activity_sorting"><div id="feedback">Existing feedback</div></section>'

        result = sanitize_generated_html(html)

        # Should only have one feedback element
        assert result.count('id="feedback"') == 1
        assert "Existing feedback" in result

    def test_adds_aria_ids_to_open_ended_inputs(self):
        """Test that data-aria-id is added to input/textarea without ids."""
        html = """
        <section data-section-type="activity_open_ended_answer">
            <input type="text" />
            <textarea></textarea>
        </section>
        """

        result = sanitize_generated_html(html)

        assert 'data-aria-id="open-ended-input-1"' in result
        assert 'data-aria-id="open-ended-input-2"' in result

    def test_skips_inputs_with_existing_ids(self):
        """Test that inputs with existing id/name/data-aria-id are not modified."""
        html = """
        <section data-section-type="activity_open_ended_answer">
            <input type="text" id="has-id" />
            <input type="text" name="has-name" />
            <input type="text" data-aria-id="has-aria" />
            <input type="text" />
        </section>
        """

        result = sanitize_generated_html(html)

        assert 'id="has-id"' in result
        assert 'name="has-name"' in result
        assert 'data-aria-id="has-aria"' in result
        # The last input without identifiers should get a generated ID
        # Index is based on all inputs encountered (4th input = index 4)
        assert 'data-aria-id="open-ended-input-' in result
        assert result.count("open-ended-input") == 1


class TestBasename:
    """Test basename helper function."""

    def test_extracts_filename_from_path(self):
        """Test basename extracts just the filename."""
        assert basename("/path/to/file.txt") == "file.txt"
        assert basename("relative/path/document.html") == "document.html"
        assert basename("/another/path/to/image.png") == "image.png"

    def test_handles_filename_without_path(self):
        """Test basename with just a filename."""
        assert basename("standalone.txt") == "standalone.txt"


class TestFormatHtml:
    """Test format_html function."""

    def test_adds_indentation_and_newlines(self):
        """Test that HTML is prettified with proper formatting."""
        html = "<html><head><title>Test</title></head><body><h1>Title</h1><p>Content</p></body></html>"

        result = format_html(html)

        # Prettified HTML should have newlines
        assert "\n" in result
        # Should have indentation (spaces or tabs)
        assert "  " in result or "\t" in result

    def test_handles_malformed_html_gracefully(self):
        """Test that BeautifulSoup fixes and formats malformed HTML."""
        html = "<div><p>Unclosed paragraph<div>Another div"

        result = format_html(html)

        # BeautifulSoup should close tags appropriately
        assert "</p>" in result or "</div>" in result
        # Should still be formatted
        assert "\n" in result
