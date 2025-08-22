import pytest
from pydantic import ValidationError

from adt_press.llm.page_sectioning import SectionResponse
from adt_press.models.section import SectionType


class TestPageSectioningValidator:
    """Test the section ID validation in SectionResponse."""

    def test_valid_sections_with_text_and_image_ids(self):
        """Test that valid sections with correct IDs pass validation."""
        sections_data = [
            {"section_id": "0", "section_type": "text_only", "part_ids": ["text-1", "text-2"]},
            {"section_id": "1", "section_type": "text_and_images", "part_ids": ["image-1", "text-3"]},
        ]

        context = {"text_ids": ["text-1", "text-2", "text-3"], "image_ids": ["image-1"]}

        # This should not raise any validation errors
        response = SectionResponse.model_validate({"reasoning": "Test reasoning", "data": sections_data}, context=context)

        assert len(response.data) == 2
        assert response.reasoning == "Test reasoning"
        assert response.data[0].section_id == "0"
        assert response.data[0].part_ids == ["text-1", "text-2"]
        assert response.data[0].section_type == SectionType.text_only

    def test_section_with_invalid_text_id(self):
        """Test that sections with invalid text IDs raise validation error."""
        sections_data = [
            {"section_id": "0", "section_type": "text_only", "part_ids": ["invalid-text-id", "text-1"]},
        ]

        context = {"text_ids": ["text-1", "text-2"], "image_ids": ["image-1"]}

        with pytest.raises(ValidationError) as exc_info:
            SectionResponse.model_validate({"reasoning": "Test", "data": sections_data}, context=context)

        error_msg = str(exc_info.value)
        assert "invalid part_id='invalid-text-id'" in error_msg
        assert "Must be one of: image-1, text-1, text-2" in error_msg
        assert "section_id='0'" in error_msg

    def test_section_with_invalid_image_id(self):
        """Test that sections with invalid image IDs raise validation error."""
        sections_data = [
            {"section_id": "1", "section_type": "text_and_images", "part_ids": ["text-1", "invalid-image-id"]},
        ]

        context = {"text_ids": ["text-1"], "image_ids": ["image-1", "image-2"]}

        with pytest.raises(ValidationError) as exc_info:
            SectionResponse.model_validate({"reasoning": "Test", "data": sections_data}, context=context)

        error_msg = str(exc_info.value)
        assert "invalid part_id='invalid-image-id'" in error_msg
        assert "Must be one of: image-1, image-2, text-1" in error_msg
        assert "section_id='1'" in error_msg

    def test_mixed_valid_and_invalid_sections(self):
        """Test sections with mix of valid and invalid IDs."""
        sections_data = [
            {"section_id": "0", "section_type": "text_only", "part_ids": ["text-1", "invalid-id"]},
            {"section_id": "1", "section_type": "text_and_images", "part_ids": ["image-1"]},
        ]

        context = {"text_ids": ["text-1"], "image_ids": ["image-1"]}

        with pytest.raises(ValidationError) as exc_info:
            SectionResponse.model_validate({"reasoning": "Test", "data": sections_data}, context=context)

        error_msg = str(exc_info.value)
        assert "invalid part_id='invalid-id'" in error_msg
        assert "section_id='0'" in error_msg

    def test_multiple_sections_same_section_id(self):
        """Test that multiple sections can have the same section_id with valid IDs."""
        sections_data = [
            {"section_id": "0", "section_type": "activity_multiple_choice", "part_ids": ["text-1", "text-2", "text-3"]},
            {"section_id": "1", "section_type": "text_and_images", "part_ids": ["image-1"]},
        ]

        context = {"text_ids": ["text-1", "text-2", "text-3"], "image_ids": ["image-1"]}

        # This should pass validation
        response = SectionResponse.model_validate({"reasoning": "Multiple choice activity", "data": sections_data}, context=context)

        assert len(response.data) == 2
        # Check that first section has all text ids
        assert response.data[0].section_id == "0"
        assert response.data[0].part_ids == ["text-1", "text-2", "text-3"]
        assert response.data[1].section_id == "1"
