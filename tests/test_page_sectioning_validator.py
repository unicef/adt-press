import pytest
from pydantic import ValidationError

from adt_press.llm.page_sectioning import SectionResponse


class TestPageSectioningValidator:
    """Test the section ID validation in SectionResponse."""

    def test_valid_sections_with_text_and_image_ids(self):
        """Test that valid sections with correct IDs pass validation."""
        sections_data = [
            {
                "section_type": "text_only",
                "background_color": "#FFFFFF",
                "text_color": "#000000",
                "part_ids": ["text-1", "text-2"],
                "page_number": None,
            },
            {
                "section_type": "text_and_images",
                "background_color": "#FFFFFF",
                "text_color": "#000000",
                "part_ids": ["image-1", "text-3"],
                "page_number": None,
            },
        ]

        context = {
            "text_ids": ["text-1", "text-2", "text-3"],
            "image_ids": ["image-1"],
            "section_types": ["text_only", "text_and_images"],  # Add section_types
        }

        # This should not raise any validation errors
        response = SectionResponse.model_validate({"reasoning": "Test reasoning", "data": sections_data}, context=context)

        assert len(response.sections) == 2
        assert response.reasoning == "Test reasoning"
        assert response.sections[0].part_ids == ["text-1", "text-2"]  # Use sections, not data
        assert response.sections[0].section_type == "text_only"

    def test_section_with_invalid_text_id(self):
        """Test that sections with invalid text IDs raise validation error."""
        sections_data = [
            {
                "section_type": "text_only",
                "background_color": "#FFFFFF",
                "text_color": "#000000",
                "part_ids": ["invalid-text-id", "text-1"],
                "page_number": 1,
            },
        ]

        context = {
            "text_ids": ["text-1", "text-2"],
            "image_ids": ["image-1"],
            "section_types": ["text_only"],  # Add section_types
        }

        with pytest.raises(ValidationError) as exc_info:
            SectionResponse.model_validate({"reasoning": "Test", "data": sections_data}, context=context)

        error_msg = str(exc_info.value)
        assert "invalid part_id='invalid-text-id'" in error_msg
        assert "Must be one of: image-1, text-1, text-2" in error_msg
        assert "Section at index 0" in error_msg

    def test_section_with_invalid_image_id(self):
        """Test that sections with invalid image IDs raise validation error."""
        sections_data = [
            {
                "section_type": "text_and_images",
                "background_color": "#FFFFFF",
                "text_color": "#000000",
                "part_ids": ["text-1", "invalid-image-id"],
                "page_number": 1,
            },
        ]

        context = {
            "text_ids": ["text-1"],
            "image_ids": ["image-1", "image-2"],
            "section_types": ["text_and_images"],  # Add section_types
        }

        with pytest.raises(ValidationError) as exc_info:
            SectionResponse.model_validate({"reasoning": "Test", "data": sections_data}, context=context)

        error_msg = str(exc_info.value)
        assert "invalid part_id='invalid-image-id'" in error_msg
        assert "Must be one of: image-1, image-2, text-1" in error_msg
        assert "Section at index 0" in error_msg

    def test_mixed_valid_and_invalid_sections(self):
        """Test sections with mix of valid and invalid IDs."""
        sections_data = [
            {
                "section_type": "text_only",
                "background_color": "#FFFFFF",
                "text_color": "#000000",
                "part_ids": ["text-1", "invalid-id"],
                "page_number": 1,
            },
            {
                "section_type": "text_and_images",
                "background_color": "#FFFFFF",
                "text_color": "#000000",
                "part_ids": ["image-1"],
                "page_number": 2,
            },
        ]

        context = {
            "text_ids": ["text-1"],
            "image_ids": ["image-1"],
            "section_types": ["text_only", "text_and_images"],  # Add section_types
        }

        with pytest.raises(ValidationError) as exc_info:
            SectionResponse.model_validate({"reasoning": "Test", "data": sections_data}, context=context)

        error_msg = str(exc_info.value)
        assert "invalid part_id='invalid-id'" in error_msg
        assert "Section at index 0" in error_msg

    def test_multiple_sections_same_section_id(self):
        """Test that multiple sections can be created with valid IDs."""
        sections_data = [
            {
                "section_type": "activity_multiple_choice",
                "background_color": "#FFFFFF",
                "text_color": "#000000",
                "part_ids": ["text-1", "text-2", "text-3"],
                "page_number": 1,
            },
            {
                "section_type": "text_and_images",
                "background_color": "#FFFFFF",
                "text_color": "#000000",
                "part_ids": ["image-1"],
                "page_number": 1,
            },
        ]

        context = {
            "text_ids": ["text-1", "text-2", "text-3"],
            "image_ids": ["image-1"],
            "section_types": ["activity_multiple_choice", "text_and_images"],  # Add section_types
        }

        # This should pass validation
        response = SectionResponse.model_validate({"reasoning": "Multiple choice activity", "data": sections_data}, context=context)

        assert len(response.sections) == 2
        # Check that first section has all text ids
        assert response.sections[0].part_ids == ["text-1", "text-2", "text-3"]
        assert response.sections[1].part_ids == ["image-1"]

    def test_section_with_invalid_section_type(self):
        """Test that sections with invalid section_type raise validation error."""
        sections_data = [
            {
                "section_type": "invalid_section_type",
                "background_color": "#FFFFFF",
                "text_color": "#000000",
                "part_ids": ["text-1"],
                "page_number": 1,
            },
        ]

        context = {
            "text_ids": ["text-1"],
            "image_ids": [],
            "section_types": ["text_only", "text_and_images"],
        }

        with pytest.raises(ValidationError) as exc_info:
            SectionResponse.model_validate({"reasoning": "Test", "data": sections_data}, context=context)

        error_msg = str(exc_info.value)
        assert "invalid section_type='invalid_section_type'" in error_msg
        assert "Section at index 0" in error_msg
