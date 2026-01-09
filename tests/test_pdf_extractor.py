"""Comprehensive but efficient integration tests for pdf_extractor tool."""

import json
import os
import sys
from pathlib import Path

import pytest

# Add the pdf_extractor tools to path
# ruff: noqa: E402
pdf_extractor_path = Path(__file__).parent.parent / "tools" / "pdf_extractor"
sys.path.insert(0, str(pdf_extractor_path))

from pdf_extractor import extract_pages_from_pdf  # type: ignore[import-not-found]

# Test PDF path
TEST_PDF = Path(__file__).parent.parent / "assets" / "raven.pdf"


@pytest.mark.skipif(not TEST_PDF.exists(), reason="Test PDF (raven.pdf) not available")
class TestPDFExtractionIntegration:
    """Integration tests covering all extraction functionality."""

    def test_normal_mode_extraction(self, tmp_path):
        """Test complete normal mode extraction pipeline."""
        output_dir = str(tmp_path / "normal")

        result = extract_pages_from_pdf(
            output_dir=output_dir,
            pdf_path=str(TEST_PDF),
            start_page=1,
            end_page=3,
            spread_mode=False,
            quiet=True,
        )

        # Validate metadata
        assert result.extract_metadata.filename == "raven.pdf"
        assert result.extract_metadata.spread_mode is False
        assert result.extract_metadata.extracted_pages == [1, 2, 3]
        assert result.extract_metadata.start_page == 1
        assert result.extract_metadata.end_page == 3
        assert isinstance(result.pdf_metadata, dict)
        assert "format" in result.pdf_metadata

        # Validate pages structure
        assert len(result.pages) == 3
        for i, page in enumerate(result.pages, 1):
            assert page.page_id == f"p{i}"
            assert page.page_number == i
            assert isinstance(page.text, str)
            assert isinstance(page.images, list)

            # Verify page image file exists
            assert os.path.exists(os.path.join(output_dir, page.page_image_path))

        # Validate image structure if any images exist
        for page in result.pages:
            for image in page.images:
                assert image.page_id == page.page_id
                assert image.image_id.startswith(f"img_{page.page_id}_")
                assert image.width > 0 and image.height > 0
                assert image.image_type in ["raster", "vector"]
                assert os.path.exists(os.path.join(output_dir, image.image_path))
                assert os.path.exists(os.path.join(output_dir, image.chart_path))

        # Validate JSON output
        json_path = os.path.join(output_dir, "test.json")
        result.save_to_file(json_path)
        with open(json_path, "r") as f:
            data = json.load(f)
        assert "extract_metadata" in data and "pdf_metadata" in data and "pages" in data

    def test_spread_mode_extraction(self, tmp_path):
        """Test complete spread mode extraction pipeline."""
        output_dir = str(tmp_path / "spread")

        result = extract_pages_from_pdf(
            output_dir=output_dir,
            pdf_path=str(TEST_PDF),
            start_page=1,
            end_page=5,
            spread_mode=True,
            quiet=True,
        )

        # Validate metadata
        assert result.extract_metadata.spread_mode is True
        assert result.extract_metadata.extracted_pages == [1, 2, 3, 4, 5]
        assert isinstance(result.pdf_metadata, dict)

        # Validate pages structure: [p1, p2_3, p4_5]
        assert len(result.pages) == 3
        assert result.pages[0].page_id == "p1"
        assert result.pages[1].page_id == "p2_3"
        assert result.pages[2].page_id == "p4_5"

        # Verify spread image files exist and have correct names
        assert os.path.exists(os.path.join(output_dir, "pages", "page_1.png"))
        assert os.path.exists(os.path.join(output_dir, "pages", "page_2_3.png"))
        assert os.path.exists(os.path.join(output_dir, "pages", "page_4_5.png"))

        # Verify images have correct page_ids for spreads
        for page in result.pages:
            for image in page.images:
                assert image.page_id == page.page_id

    def test_spread_mode_with_subset_range(self, tmp_path):
        """Test spread mode respects global boundaries with subset ranges."""
        # Test pages 2-3 (should be single spread)
        output_dir = str(tmp_path / "spread_2_3")
        result = extract_pages_from_pdf(
            output_dir=output_dir,
            pdf_path=str(TEST_PDF),
            start_page=2,
            end_page=3,
            spread_mode=True,
            quiet=True,
        )
        assert len(result.pages) == 1
        assert result.pages[0].page_id == "p2_3"

        # Test pages 3-4 (should be two separate pages)
        output_dir = str(tmp_path / "spread_3_4")
        result = extract_pages_from_pdf(
            output_dir=output_dir,
            pdf_path=str(TEST_PDF),
            start_page=3,
            end_page=4,
            spread_mode=True,
            quiet=True,
        )
        assert len(result.pages) == 2
        assert result.pages[0].page_id == "p3"
        assert result.pages[1].page_id == "p4"

    def test_spread_image_dimensions(self, tmp_path):
        """Test that spread images are stitched correctly."""
        from PIL import Image

        # Extract pages 2-3 separately in normal mode
        normal_dir = str(tmp_path / "normal")
        normal_result = extract_pages_from_pdf(
            output_dir=normal_dir,
            pdf_path=str(TEST_PDF),
            start_page=2,
            end_page=3,
            spread_mode=False,
            quiet=True,
        )

        # Extract pages 1-3 in spread mode to get 2-3 spread
        spread_dir = str(tmp_path / "spread")
        spread_result = extract_pages_from_pdf(
            output_dir=spread_dir,
            pdf_path=str(TEST_PDF),
            start_page=1,
            end_page=3,
            spread_mode=True,
            quiet=True,
        )

        # Load images
        img_page2 = Image.open(os.path.join(normal_dir, normal_result.pages[0].page_image_path))
        img_page3 = Image.open(os.path.join(normal_dir, normal_result.pages[1].page_image_path))
        img_spread = Image.open(os.path.join(spread_dir, spread_result.pages[1].page_image_path))

        # Spread width should equal sum of individual widths
        assert img_spread.width == img_page2.width + img_page3.width
        assert img_spread.height >= max(img_page2.height, img_page3.height)

    def test_spread_image_has_content_on_both_sides(self, tmp_path):
        """Test that spread images have content on both left and right sides (not blank)."""
        from PIL import Image

        # Extract pages 2-3 as a spread
        spread_dir = str(tmp_path / "spread")
        spread_result = extract_pages_from_pdf(
            output_dir=spread_dir,
            pdf_path=str(TEST_PDF),
            start_page=2,
            end_page=3,
            spread_mode=True,
            quiet=True,
        )

        # Load the spread image
        img_path = os.path.join(spread_dir, spread_result.pages[0].page_image_path)
        img = Image.open(img_path)
        width, height = img.size

        # Sample pixels from left and right halves to check for non-white content
        def count_non_white_pixels(img, x_start, x_end, y_start, y_end, step=20):
            """Count non-white pixels in a region."""
            count = 0
            for y in range(y_start, y_end, step):
                for x in range(x_start, x_end, step):
                    if x < img.width and y < img.height:
                        pixel = img.getpixel((x, y))
                        if pixel != (255, 255, 255):
                            count += 1
            return count

        # Check left half (first page)
        left_non_white = count_non_white_pixels(img, 0, width // 2, 0, height)

        # Check right half (second page)
        right_non_white = count_non_white_pixels(img, width // 2, width, 0, height)

        # Both halves should have content (not be blank)
        assert left_non_white > 0, "Left side of spread is blank"
        assert right_non_white > 0, "Right side of spread is blank"

        # Ensure the spread is wider than a single page would be
        assert width > 1000, "Spread image seems too narrow"

    def test_error_handling(self, tmp_path):
        """Test error handling for invalid inputs."""
        output_dir = str(tmp_path / "errors")

        # Invalid page range
        with pytest.raises(ValueError, match="out of range"):
            extract_pages_from_pdf(
                output_dir=output_dir,
                pdf_path=str(TEST_PDF),
                start_page=9999,
                end_page=10000,
                spread_mode=False,
                quiet=True,
            )

        # End < start
        with pytest.raises(ValueError, match="cannot be less than"):
            extract_pages_from_pdf(
                output_dir=output_dir,
                pdf_path=str(TEST_PDF),
                start_page=5,
                end_page=2,
                spread_mode=False,
                quiet=True,
            )

    def test_automatic_directory_creation(self, tmp_path):
        """Test that output directories are created automatically."""
        output_dir = str(tmp_path / "nested" / "deep" / "path")

        extract_pages_from_pdf(
            output_dir=output_dir,
            pdf_path=str(TEST_PDF),
            start_page=1,
            end_page=1,
            spread_mode=False,
            quiet=True,
        )

        assert os.path.exists(os.path.join(output_dir, "pages"))
        assert os.path.exists(os.path.join(output_dir, "images"))

    def test_end_page_zero_extracts_all(self, tmp_path):
        """Test that end_page=0 extracts to end of document."""
        output_dir = str(tmp_path / "all_pages")

        result = extract_pages_from_pdf(
            output_dir=output_dir,
            pdf_path=str(TEST_PDF),
            start_page=1,
            end_page=0,
            spread_mode=False,
            quiet=True,
        )

        total_pages = result.extract_metadata.total_pages
        assert len(result.pages) == total_pages
        assert result.extract_metadata.end_page == total_pages
