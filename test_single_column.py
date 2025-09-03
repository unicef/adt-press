#!/usr/bin/env python3

"""Quick test to verify single-column validation works."""

from adt_press.llm.web_generation_twoColumns import GenerationResponse, Row, Column

def test_single_column_validation():
    """Test that single column layouts are accepted for image-only pages."""
    
    # Create a single column layout with image
    single_column_data = {
        "rows": [
            {
                "columns": [
                    {
                        "span": 5,
                        "background_color": "#ffffff", 
                        "color": "#000000",
                        "parts": ["img_1"]
                    }
                ]
            }
        ]
    }
    
    # Create validation context with only image IDs (no text)
    validation_context = {
        "text_ids": [],  # No text - should allow single column
        "image_ids": ["img_1"]
    }
    
    try:
        response = GenerationResponse.model_validate(
            single_column_data,
            context=validation_context
        )
        print("✅ Single column validation PASSED")
        print(f"Response: {response}")
        return True
    except Exception as e:
        print(f"❌ Single column validation FAILED: {e}")
        return False

def test_single_column_with_text_should_fail():
    """Test that single column layouts are rejected when text is present."""
    
    # Create a single column layout
    single_column_data = {
        "rows": [
            {
                "columns": [
                    {
                        "span": 5,
                        "background_color": "#ffffff",
                        "color": "#000000", 
                        "parts": ["img_1"]
                    }
                ]
            }
        ]
    }
    
    # Create validation context WITH text IDs - should fail
    validation_context = {
        "text_ids": ["t_1"],  # Has text - should reject single column
        "image_ids": ["img_1"]
    }
    
    try:
        response = GenerationResponse.model_validate(
            single_column_data,
            context=validation_context
        )
        print("❌ Single column with text validation FAILED - should have been rejected")
        return False
    except Exception as e:
        print(f"✅ Single column with text correctly REJECTED: {e}")
        return True

if __name__ == "__main__":
    print("Testing single column validation...")
    test1 = test_single_column_validation()
    test2 = test_single_column_with_text_should_fail()
    
    if test1 and test2:
        print("\n🎉 All validation tests passed!")
    else:
        print("\n💥 Some validation tests failed!")
