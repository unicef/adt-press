import pytest
from pydantic import ValidationError

from adt_press.llm.web_generation_html import GenerationResponse


class TestHTMLDataIdValidator:
    """Test the HTML data-id validation in GenerationResponse."""

    def test_valid_html_with_text_and_image_ids(self):
        """Test that valid HTML with correct data-ids passes validation."""
        html_content = """
        <div id="content" class="container">
        <section><div data-id="text-1">This is some text</div>
        <p data-id="text-2">Another paragraph</p>
        <img src="test.jpg" data-id="image-1" alt="Test image">
        </section>
        </div>
        """

        # Create context with valid IDs
        context = {"text_ids": ["text-1", "text-2"], "image_ids": ["image-1"]}

        # This should not raise any validation errors
        response = GenerationResponse.model_validate({"reasoning": "Test reasoning", "content": html_content}, context=context)

        assert response.content == html_content
        assert response.reasoning == "Test reasoning"

    def test_text_element_missing_data_id(self):
        """Test that text elements without data-id raise validation error."""
        html_content = """<div id="content" class="container">
        <section><div data-id="text-1">This is some text</div>
        <p>Another paragraph</p>
        <img src="test.jpg" data-id="image-1" alt="Test image">
        </section>
        </div>"""

        context = {"text_ids": ["text-1"], "image_ids": ["image-1"]}

        with pytest.raises(ValidationError) as exc_info:
            GenerationResponse.model_validate({"reasoning": "Test", "content": html_content}, context=context)

        error_msg = str(exc_info.value)
        assert "missing required data-id attribute" in error_msg
        assert "div" in error_msg

    def test_image_element_missing_data_id(self):
        """Test that img elements without data-id raise validation error."""
        html_content = """
        <div id="content" class="container">
        <section><div data-id="text-1">This is some text</div>
        <p data-id="text-1">Another paragraph</p>
        <img src="test.jpg" alt="Test image">
        </section>
        </div>
        """
        context = {"text_ids": ["text-1"], "image_ids": ["image-1"]}

        with pytest.raises(ValidationError) as exc_info:
            GenerationResponse.model_validate({"reasoning": "Test", "content": html_content}, context=context)

        error_msg = str(exc_info.value)
        assert "Image element is missing required data-id attribute" in error_msg

    def test_text_element_invalid_data_id(self):
        """Test that text elements with invalid data-id raise validation error."""
        html_content = """
        <div id="content" class="container">
        <section><div data-id="text-1">This is some text</div>
        <p data-id="invalid-text-id">Another paragraph</p>
        <img data-id="image-1" src="test.jpg" alt="Test image">
        </section>
        </div>
        """

        context = {"text_ids": ["text-1", "text-2"], "image_ids": ["image-1"]}

        with pytest.raises(ValidationError) as exc_info:
            GenerationResponse.model_validate({"reasoning": "Test", "content": html_content}, context=context)

        error_msg = str(exc_info.value)
        assert "invalid data-id='invalid-text-id'" in error_msg
        assert "Must be one of text IDs: text-1, text-2" in error_msg

    def test_image_element_invalid_data_id(self):
        """Test that img elements with invalid data-id raise validation error."""
        html_content = """
        <div id="content" class="container">
        <section><div data-id="text-1">This is some text</div>
        <p data-id="text-1">Another paragraph</p>
        <img data-id="invalid-image-id" src="test.jpg" alt="Test image">
        </section>
        </div>
        """

        context = {"text_ids": ["text-1"], "image_ids": ["image-1", "image-2"]}

        with pytest.raises(ValidationError) as exc_info:
            GenerationResponse.model_validate({"reasoning": "Test", "content": html_content}, context=context)

        error_msg = str(exc_info.value)
        assert "invalid data-id='invalid-image-id'" in error_msg
        assert "Must be one of image IDs: image-1, image-2" in error_msg

    def test_mixed_valid_and_invalid_elements(self):
        """Test HTML with mix of valid and invalid elements."""
        html_content = """
        <div data-id="text-1">Valid text</div>
        <p>Invalid text without data-id</p>
        <img src="test.jpg" data-id="image-1" alt="Valid image">
        """

        context = {"text_ids": ["text-1"], "image_ids": ["image-1"]}

        with pytest.raises(ValidationError) as exc_info:
            GenerationResponse.model_validate({"reasoning": "Test", "content": html_content}, context=context)

        error_msg = str(exc_info.value)
        assert "missing required data-id attribute" in error_msg
        assert "p" in error_msg

    def test_nested_elements_with_text(self):
        """Test that nested elements with direct text content are validated."""
        html_content = """
        <div id="content" class="container">
        <section><div data-id="text-1">This is some text</div>
        <div><p data-id="text-1">Another paragraph</p></div>
        </section>
        </div>
        """

        context = {"text_ids": ["text-1", "text-2"], "image_ids": []}

        # This should pass validation
        response = GenerationResponse.model_validate({"reasoning": "Test", "content": html_content}, context=context)

        assert response.content == html_content

    def test_elements_with_only_whitespace_ignored(self):
        """Test that elements with only whitespace don't require data-id."""
        html_content = """
        <div id="content" class="container">
        <section><div data-id="text-1">This is some text</div>
        <div><p data-id="text-1">Another paragraph</p></div>
        <div>


        </div>
        </section>
        </div>
        """

        context = {"text_ids": ["text-1"], "image_ids": []}

        # This should pass validation (whitespace-only div is ignored)
        response = GenerationResponse.model_validate({"reasoning": "Test", "content": html_content}, context=context)

        assert response.content == html_content

    def test_text_using_image_id(self):
        """Test that text elements cannot use image IDs."""
        html_content = """
        <div id="content" class="container">
        <section><div data-id="image-1">This is some text</div>
        <div><p data-id="text-1">Another paragraph</p></div>
        </section>
        </div>
        """

        context = {"text_ids": ["text-1"], "image_ids": ["image-1"]}

        with pytest.raises(ValidationError) as exc_info:
            GenerationResponse.model_validate({"reasoning": "Test", "content": html_content}, context=context)

        error_msg = str(exc_info.value)
        assert "invalid data-id='image-1'" in error_msg
        assert "Must be one of text IDs: text-1" in error_msg

    def test_image_using_text_id(self):
        """Test that image elements cannot use text IDs."""
        html_content = """
        <div id="content" class="container">
        <section><div data-id="text-1">This is some text</div>
        <img data-id="text-1" src="test.jpg" alt="Test image">
        </section>
        </div>
        """

        context = {"text_ids": ["text-1"], "image_ids": ["image-1"]}

        with pytest.raises(ValidationError) as exc_info:
            GenerationResponse.model_validate({"reasoning": "Test", "content": html_content}, context=context)

        error_msg = str(exc_info.value)
        assert "invalid data-id='text-1'" in error_msg
        assert "Must be one of image IDs: image-1" in error_msg
