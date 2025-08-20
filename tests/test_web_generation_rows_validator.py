import pytest
from pydantic import ValidationError

from adt_press.llm.web_generation_rows import Column, GenerationResponse, Row


class TestRowsDataIdValidator:
    """Test the data-id validation in GenerationResponse for rows."""

    def test_valid_rows_with_text_and_image_ids(self):
        """Test that valid rows with correct part IDs pass validation."""
        rows = [
            Row(columns=[Column(span=6, parts=["text-1", "image-1"]), Column(span=6, parts=["text-2"])]),
            Row(columns=[Column(span=12, parts=["image-2", "text-3"])]),
        ]

        # Create context with valid IDs
        context = {"text_ids": ["text-1", "text-2", "text-3"], "image_ids": ["image-1", "image-2"]}

        # This should not raise any validation errors
        response = GenerationResponse.model_validate({"reasoning": "Test reasoning", "rows": rows}, context=context)

        assert len(response.rows) == 2
        assert response.reasoning == "Test reasoning"

    def test_empty_column_parts_raises_error(self):
        """Test that columns with empty parts list raise validation error."""
        rows = [
            Row(
                columns=[
                    Column(span=6, parts=[]),  # Empty parts
                    Column(span=6, parts=["text-1"]),
                ]
            )
        ]

        context = {"text_ids": ["text-1"], "image_ids": ["image-1"]}

        with pytest.raises(ValidationError) as exc_info:
            GenerationResponse.model_validate({"reasoning": "Test", "rows": rows}, context=context)

        error_msg = str(exc_info.value)
        assert "has an empty column" in error_msg

    def test_duplicate_parts_raises_error(self):
        """Test that duplicate part IDs raise validation error."""
        rows = [
            Row(
                columns=[
                    Column(span=6, parts=["text-1", "text-1"]),  # Duplicate
                    Column(span=6, parts=["text-2"]),
                ]
            )
        ]

        context = {"text_ids": ["text-1", "text-2"], "image_ids": []}

        with pytest.raises(ValidationError) as exc_info:
            GenerationResponse.model_validate({"reasoning": "Test", "rows": rows}, context=context)

        error_msg = str(exc_info.value)
        assert "Duplicate part 'text-1' found" in error_msg

    def test_duplicate_parts_across_columns_raises_error(self):
        """Test that duplicate part IDs across different columns raise validation error."""
        rows = [
            Row(
                columns=[
                    Column(span=6, parts=["text-1"]),
                    Column(span=6, parts=["text-1"]),  # Duplicate across columns
                ]
            )
        ]

        context = {"text_ids": ["text-1"], "image_ids": []}

        with pytest.raises(ValidationError) as exc_info:
            GenerationResponse.model_validate({"reasoning": "Test", "rows": rows}, context=context)

        error_msg = str(exc_info.value)
        assert "Duplicate part 'text-1' found" in error_msg

    def test_duplicate_parts_across_rows_raises_error(self):
        """Test that duplicate part IDs across different rows raise validation error."""
        rows = [
            Row(columns=[Column(span=12, parts=["text-1"])]),
            Row(
                columns=[
                    Column(span=12, parts=["text-1"])  # Duplicate across rows
                ]
            ),
        ]

        context = {"text_ids": ["text-1"], "image_ids": []}

        with pytest.raises(ValidationError) as exc_info:
            GenerationResponse.model_validate({"reasoning": "Test", "rows": rows}, context=context)

        error_msg = str(exc_info.value)
        assert "Duplicate part 'text-1' found" in error_msg

    def test_invalid_part_id_raises_error(self):
        """Test that invalid part IDs raise validation error."""
        rows = [Row(columns=[Column(span=6, parts=["invalid-id"]), Column(span=6, parts=["text-1"])])]

        context = {"text_ids": ["text-1", "text-2"], "image_ids": ["image-1"]}

        with pytest.raises(ValidationError) as exc_info:
            GenerationResponse.model_validate({"reasoning": "Test", "rows": rows}, context=context)

        error_msg = str(exc_info.value)
        assert "Part 'invalid-id'" in error_msg
        assert "has invalid ID" in error_msg
        assert "Must be one of:" in error_msg

    def test_mixed_valid_and_invalid_parts(self):
        """Test rows with mix of valid and invalid part IDs."""
        rows = [
            Row(
                columns=[
                    Column(span=4, parts=["text-1"]),  # Valid
                    Column(span=4, parts=["invalid-id"]),  # Invalid
                    Column(span=4, parts=["image-1"]),  # Valid
                ]
            )
        ]

        context = {"text_ids": ["text-1"], "image_ids": ["image-1"]}

        with pytest.raises(ValidationError) as exc_info:
            GenerationResponse.model_validate({"reasoning": "Test", "rows": rows}, context=context)

        error_msg = str(exc_info.value)
        assert "Part 'invalid-id'" in error_msg
        assert "has invalid ID" in error_msg
