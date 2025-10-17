#!/usr/bin/env python3
# ruff: noqa T201
"""
Standalone PDF Extractor Tool

This script extracts pages, text, and images from PDF files using PyMuPDF.

Usage:
    python pdf_extractor.py --pdf_path document.pdf --start_page 1 --end_page 5 --output_dir ./output
"""

import argparse
import os
import sys
import traceback
from datetime import datetime

import pymupdf  # PyMuPDF

from models import Image, Metadata, Page, PDFExtract
from utils import matplotlib_chart, render_drawings, write_file

# We need to set this zoom for PyMuPDF or the image is pixelated.
FITZ_ZOOM = 2
FITZ_MAT = pymupdf.Matrix(FITZ_ZOOM, FITZ_ZOOM)


def extract_pages_from_pdf(output_dir: str, pdf_path: str, start_page: int, end_page: int) -> PDFExtract:
    """
    Extract pages from PDF file and return structured data.

    Args:
        output_dir: Directory to save extracted images
        pdf_path: Path to the PDF file
        start_page: Starting page number (1-based)
        end_page: Ending page number (1-based, 0 means end of document)

    Returns:
        PDFExtract containing all extracted data
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Create subdirectories for organization
    pages_dir = os.path.join(output_dir, "pages")
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(pages_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    # Open PDF
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")

    # Determine page range
    total_pages = len(doc)
    end_page = min(end_page, total_pages) if end_page > 0 else total_pages
    start_page = 1 if start_page == 0 else start_page

    # Validate page range
    if start_page < 1 or start_page > total_pages:
        raise ValueError(f"Start page {start_page} is out of range (1-{total_pages})")
    if end_page < start_page:
        raise ValueError(f"End page {end_page} cannot be less than start page {start_page}")

    pages = []
    extracted_page_numbers = []

    for page_index in range(start_page - 1, end_page):
        fitz_page = doc[page_index]
        page_number = page_index + 1
        page_id = f"p{page_number}"
        extracted_page_numbers.append(page_number)

        # Extract full page image
        page_image = fitz_page.get_pixmap(matrix=FITZ_MAT)
        page_image_filename = f"page_{page_number}.png"
        page_image_path = os.path.join(pages_dir, page_image_filename)
        write_file(page_image_path, page_image.tobytes(output="png"))

        # Extract text
        page_text = fitz_page.get_text()

        # Extract images
        images = []
        image_index = 0

        # Extract raster images
        for img in fitz_page.get_images(full=True):
            pix = pymupdf.Pixmap(doc, img[0])
            pix_rgb = pymupdf.Pixmap(pymupdf.csRGB, pix)
            img_id = f"img_{page_id}_r{image_index}"
            img_bytes = pix_rgb.tobytes(output="png")

            # Save original image
            img_filename = f"{img_id}.png"
            img_path = os.path.join(images_dir, img_filename)
            write_file(img_path, img_bytes)

            # Save chart version
            chart_filename = f"{img_id}_chart.png"
            chart_path = os.path.join(images_dir, chart_filename)
            chart_bytes = matplotlib_chart(img_bytes)
            write_file(chart_path, chart_bytes)

            images.append(
                Image(
                    image_id=img_id,
                    page_id=page_id,
                    index=image_index,
                    image_path=os.path.join("images", img_filename),
                    chart_path=os.path.join("images", chart_filename),
                    width=pix_rgb.width,
                    height=pix_rgb.height,
                    image_type="raster",
                )
            )
            image_index += 1

            # Clean up pixmaps
            pix_rgb = None
            pix = None

        # Extract vector drawings (extended=True to get clipping info)
        drawings = fitz_page.get_drawings(extended=True)
        vector_images = render_drawings(drawings, margin_allowance=0, overlap_threshold=400)

        for vector_img in vector_images:
            img_id = f"img_{page_id}_v{image_index}"

            # Save vector image
            vector_filename = f"{img_id}.png"
            vector_path = os.path.join(images_dir, vector_filename)
            write_file(vector_path, vector_img.image)

            # Save chart version
            chart_filename = f"{img_id}_chart.png"
            chart_path = os.path.join(images_dir, chart_filename)
            chart_bytes = matplotlib_chart(vector_img.image)
            write_file(chart_path, chart_bytes)

            images.append(
                Image(
                    image_id=img_id,
                    page_id=page_id,
                    index=image_index,
                    image_path=os.path.join("images", vector_filename),
                    chart_path=os.path.join("images", chart_filename),
                    width=vector_img.width,
                    height=vector_img.height,
                    image_type="vector",
                )
            )
            image_index += 1

        # Create page object
        pages.append(
            Page(
                page_id=page_id,
                page_number=page_number,
                page_image_path=os.path.join("pages", page_image_filename),
                text=page_text,
                images=images,
            )
        )

    # Create metadata
    pdf_metadata = Metadata(
        filename=os.path.basename(pdf_path),
        total_pages=total_pages,
        extracted_pages=extracted_page_numbers,
        extraction_timestamp=datetime.now().isoformat(),
        start_page=start_page,
        end_page=end_page,
    )

    # Create final result
    return PDFExtract(pdf_metadata=pdf_metadata, pages=pages)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract pages, text, and images from PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_extractor.py --pdf_path document.pdf --output_dir ./output
  python pdf_extractor.py --pdf_path doc.pdf --start_page 1 --end_page 5 --output_dir ./output
        """,
    )

    parser.add_argument("--pdf_path", required=True, help="Path to the PDF file to extract")

    parser.add_argument("--output_dir", required=True, help="Directory to save extracted content")

    parser.add_argument("--start_page", type=int, default=1, help="Starting page number (1-based, default: 1)")

    parser.add_argument(
        "--end_page", type=int, default=0, help="Ending page number (1-based, 0 means end of document, default: 0)"
    )

    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")

    args = parser.parse_args()

    # Validate inputs
    if not os.path.isfile(args.pdf_path):
        print(f"Error: PDF file not found: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)

    try:
        if not args.quiet:
            print(f"Extracting from: {args.pdf_path}")
            print(f"Page range: {args.start_page} to {'end' if args.end_page == 0 else args.end_page}")
            print(f"Output directory: {args.output_dir}")

        # Perform extraction
        result = extract_pages_from_pdf(
            output_dir=args.output_dir, pdf_path=args.pdf_path, start_page=args.start_page, end_page=args.end_page
        )

        # Save results to JSON
        results_path = os.path.join(args.output_dir, "pdf_extract.json")
        result.save_to_file(results_path)

        if not args.quiet:
            print("✓ Extraction complete!")
            print(f"  - Extracted {len(result.pages)} pages")
            print(f"  - Found {sum(len(page.images) for page in result.pages)} images")
            print(f"  - Results saved to: {results_path}")

    except Exception as e:
        print(f"\nError during extraction: {e}", file=sys.stderr)
        print("\nFull traceback:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
