#!/usr/bin/env python3
"""Test script to verify the text-only validator changes work correctly."""

from adt_press.llm.web_generation_twoColumns import GenerationResponse, Row, Column


def test_text_only_validation():
    """Test that text-only single column layout is now allowed."""
    
    # Simulate validation context for a text-only page
    validation_context = {
        "text_ids": ["txt_1", "txt_2"],
        "image_ids": [],  # No images
        "section_type": "text_only"
    }
    
    # Test single column layout with only text (should pass now)
    single_column_text = GenerationResponse(
        rows=[
            Row(
                columns=[
                    Column(
                        span=5,
                        background_color="#ffffff",
                        color="#000000",
                        parts=["txt_1", "txt_2"]
                    )
                ]
            )
        ]
    )
    
    try:
        # This should not raise an exception anymore
        single_column_text.model_validate(
            single_column_text.model_dump(),
            context=validation_context
        )
        print("✅ SUCCESS: Single column text-only layout is now allowed")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_mixed_content_validation():
    """Test that mixed content still fails in single column."""
    
    # Simulate validation context for a page with both text and images
    validation_context = {
        "text_ids": ["txt_1"],
        "image_ids": ["img_1"],
        "section_type": "text_and_images"
    }
    
    # Test single column layout with both text and images (should fail)
    single_column_mixed = GenerationResponse(
        rows=[
            Row(
                columns=[
                    Column(
                        span=5,
                        background_color="#ffffff",
                        color="#000000",
                        parts=["txt_1", "img_1"]
                    )
                ]
            )
        ]
    )
    
    try:
        single_column_mixed.model_validate(
            single_column_mixed.model_dump(),
            context=validation_context
        )
        print("❌ FAILED: Single column mixed content should not be allowed")
        return False
    except Exception as e:
        print(f"✅ SUCCESS: Single column mixed content correctly rejected: {e}")
        return True


if __name__ == "__main__":
    print("Testing text-only validator changes...")
    
    success1 = test_text_only_validation()
    success2 = test_mixed_content_validation()
    
    if success1 and success2:
        print("\n🎉 All validator tests passed! Text-only pages should now work correctly.")
    else:
        print("\n❌ Some tests failed. Check the validator logic.")
