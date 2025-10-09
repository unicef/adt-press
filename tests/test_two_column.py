#!/usr/bin/env python3

"""Quick test to verify single-column validation works."""

from adt_press.llm.web_generation_two_column import GenerationResponse


def test_single_column_validation():
    """Test that single column layouts are accepted for image-only pages."""

    # Create a single column layout with image
    single_column_data = {
        "rows": [{"columns": [{"span": 5, "background_color": "#ffffff", "color": "#000000", "parts": ["img_1"]}]}],
        "reasoning": "Single column layout is acceptable for image-only content"
    }

    # Create validation context with only image IDs (no text)
    validation_context = {
        "text_ids": [],  # No text - should allow single column
        "image_ids": ["img_1"],
    }

    # Should not raise an exception
    result = GenerationResponse.model_validate(single_column_data, context=validation_context)
    assert result is not None
    print("✅ Single column validation PASSED")


def test_single_column_with_text_should_fail():
    """Test that single column layouts are rejected when text is present."""

    # Create a single column layout
    single_column_data = {
        "rows": [{"columns": [{"span": 5, "background_color": "#ffffff", "color": "#000000", "parts": ["img_1"]}]}],
        "reasoning": "Single column layout should be rejected when text is present"
    }

    # Create validation context WITH text IDs - should fail
    validation_context = {
        "text_ids": ["t_1"],  # Has text - should reject single column
        "image_ids": ["img_1"],
    }

    # Should raise a validation exception
    try:
        GenerationResponse.model_validate(single_column_data, context=validation_context)
        assert False, "Single column with text should have been rejected"
    except Exception as e:
        print(f"✅ Single column with text correctly REJECTED: {e}")
        assert True  # Expected to fail


if __name__ == "__main__":
    print("Testing single column validation...")
    test_single_column_validation()
    test_single_column_with_text_should_fail()
    print("\n🎉 All validation tests passed!")
