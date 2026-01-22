import pytest
from pydantic import ValidationError

from adt_press.llm.web_generation_edit import WebEditResponse


class TestWebEditHTMLValidator:
    """Test the HTML data-id validation in WebEditResponse using table-driven tests."""

    @pytest.mark.parametrize(
        "name,html_content,context,should_pass,expected_errors",
        [
            (
                "valid_html_with_text_and_image_ids",
                """
                <div id="content" class="container">
                <section><div data-id="text-1">This is some text</div>
                <p data-id="text-2">Another paragraph</p>
                <img src="test.jpg" data-id="image-1" alt="Test image">
                </section>
                </div>
                """,
                {"text_ids": ["text-1", "text-2"], "image_ids": ["image-1"]},
                True,
                [],
            ),
            (
                "text_element_missing_data_id",
                """<div id="content" class="container">
                <section><div data-id="text-1">This is some text</div>
                <p>Another paragraph</p>
                <img src="test.jpg" data-id="image-1" alt="Test image">
                </section>
                </div>""",
                {"text_ids": ["text-1"], "image_ids": ["image-1"]},
                False,
                ["missing required data-id attribute", "div"],
            ),
            (
                "image_element_missing_data_id",
                """
                <div id="content" class="container">
                <section><div data-id="text-1">This is some text</div>
                <p data-id="text-1">Another paragraph</p>
                <img src="test.jpg" alt="Test image">
                </section>
                </div>
                """,
                {"text_ids": ["text-1"], "image_ids": ["image-1"]},
                False,
                ["Image element is missing required data-id attribute"],
            ),
            (
                "text_element_invalid_data_id",
                """
                <div id="content" class="container">
                <section><div data-id="text-1">This is some text</div>
                <p data-id="invalid-text-id">Another paragraph</p>
                <img data-id="image-1" src="test.jpg" alt="Test image">
                </section>
                </div>
                """,
                {"text_ids": ["text-1", "text-2"], "image_ids": ["image-1"]},
                False,
                ["invalid data-id='invalid-text-id'", "Must be one of text IDs: text-1, text-2"],
            ),
            (
                "image_element_invalid_data_id",
                """
                <div id="content" class="container">
                <section><div data-id="text-1">This is some text</div>
                <p data-id="text-1">Another paragraph</p>
                <img data-id="invalid-image-id" src="test.jpg" alt="Test image">
                </section>
                </div>
                """,
                {"text_ids": ["text-1"], "image_ids": ["image-1", "image-2"]},
                False,
                ["invalid data-id='invalid-image-id'", "Must be one of image IDs: image-1, image-2"],
            ),
            (
                "empty_html_content",
                "",
                {"text_ids": ["text-1"], "image_ids": ["image-1"]},
                False,
                ["Generated HTML content is empty"],
            ),
            (
                "whitespace_only_html_content",
                "   \n\n  \t  ",
                {"text_ids": ["text-1"], "image_ids": ["image-1"]},
                False,
                ["Generated HTML content is empty"],
            ),
            (
                "text_using_image_id",
                """
                <div id="content" class="container">
                <section><div data-id="image-1">This is some text</div>
                <div><p data-id="text-1">Another paragraph</p></div>
                </section>
                </div>
                """,
                {"text_ids": ["text-1"], "image_ids": ["image-1"]},
                False,
                ["invalid data-id='image-1'", "Must be one of text IDs: text-1"],
            ),
            (
                "image_using_text_id",
                """
                <div id="content" class="container">
                <section><div data-id="text-1">This is some text</div>
                <img data-id="text-1" src="test.jpg" alt="Test image">
                </section>
                </div>
                """,
                {"text_ids": ["text-1"], "image_ids": ["image-1"]},
                False,
                ["invalid data-id='text-1'", "Must be one of image IDs: image-1"],
            ),
            (
                "missing_main_content_container",
                """
                <section><div data-id="text-1">This is some text</div></section>
                """,
                {"text_ids": ["text-1"], "image_ids": []},
                False,
                ["missing the main <div id='content'> container"],
            ),
            (
                "missing_section_element",
                """
                <div id="content" class="container">
                <div data-id="text-1">This is some text</div>
                </div>
                """,
                {"text_ids": ["text-1"], "image_ids": []},
                False,
                ["must include a <section> element"],
            ),
        ],
    )
    def test_html_validation(self, name, html_content, context, should_pass, expected_errors):
        """Table-driven test for HTML validation."""
        if should_pass:
            # Test should pass validation
            response = WebEditResponse.model_validate({"reasoning": "Test reasoning", "html": html_content}, context=context)
            assert response.html == html_content
            assert response.reasoning == "Test reasoning"
        else:
            # Test should fail validation
            with pytest.raises(ValidationError) as exc_info:
                WebEditResponse.model_validate({"reasoning": "Test", "html": html_content}, context=context)

            error_msg = str(exc_info.value)
            for expected_error in expected_errors:
                assert expected_error in error_msg, f"Expected error '{expected_error}' not found in: {error_msg}"
