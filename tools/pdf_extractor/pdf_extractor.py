#!/usr/bin/env python3
# ruff: noqa T201
"""
Standalone PDF Extractor Tool

This script extracts pages, text, and images from PDF files using PyMuPDF.

Usage:
    python pdf_extractor.py --pdf_path document.pdf --start_page 1 --end_page 5 --output_dir ./output
"""

import argparse
import io
import os
import sys
import traceback
from datetime import datetime

import pymupdf  # PyMuPDF
from PIL import Image as PILImage

from models import Image, Metadata, Page, PDFExtract
from utils import matplotlib_chart, render_drawings, write_file

# We need to set this zoom for PyMuPDF or the image is pixelated.
FITZ_ZOOM = 2
FITZ_MAT = pymupdf.Matrix(FITZ_ZOOM, FITZ_ZOOM)


def get_page_groupings(start_page: int, end_page: int, spread_mode: bool) -> list[tuple[int, ...]]:
    """
    Generate page groupings for extraction.

    In spread mode, spreads are determined by global page numbers, not the extraction range:
    - Page 1 is always solo (cover)
    - Pages 2-3, 4-5, 6-7, etc. are spreads
    In normal mode, each page is solo.

    Args:
        start_page: Starting page number (1-based)
        end_page: Ending page number (1-based)
        spread_mode: Whether to use spread mode

    Returns:
        List of tuples, where each tuple contains page numbers to process together.
        Examples:
            Normal mode, pages 1-5: [(1,), (2,), (3,), (4,), (5,)]
            Spread mode, pages 1-5: [(1,), (2, 3), (4, 5)]
            Spread mode, pages 2-3: [(2, 3)]  # This is a spread boundary
            Spread mode, pages 3-4: [(3,), (4,)]  # Crosses spread boundary
    """
    if not spread_mode:
        return [(page,) for page in range(start_page, end_page + 1)]

    groupings = []
    current = start_page

    while current <= end_page:
        if current == 1:
            # Page 1 is always solo (cover)
            groupings.append((1,))
            current += 1
        elif current % 2 == 0:
            # Even page: check if we can pair with next odd page
            if current + 1 <= end_page:
                # Pair even page with following odd page (2-3, 4-5, 6-7, etc.)
                groupings.append((current, current + 1))
                current += 2
            else:
                # Even page at end of range, solo
                groupings.append((current,))
                current += 1
        else:
            # Odd page (not page 1): solo because it's not paired with preceding even
            groupings.append((current,))
            current += 1

    return groupings


def stitch_page_images(doc: pymupdf.Document, page_indices: list[int]) -> bytes:
    """
    Stitch multiple page images together horizontally.

    Args:
        doc: PyMuPDF document
        page_indices: List of 0-based page indices to stitch

    Returns:
        PNG bytes of stitched image
    """
    if len(page_indices) == 1:
        # Single page, just return the pixmap
        page = doc[page_indices[0]]
        pix = page.get_pixmap(matrix=FITZ_MAT)
        return pix.tobytes(output="png")

    # Get pixmaps for all pages
    pixmaps = [doc[idx].get_pixmap(matrix=FITZ_MAT) for idx in page_indices]

    # Convert pixmaps to PIL Images for easier manipulation
    pil_images = []
    for pix in pixmaps:
        img = PILImage.frombytes("RGB", (pix.width, pix.height), pix.samples)
        pil_images.append(img)

    # Calculate dimensions
    total_width = sum(img.width for img in pil_images)
    max_height = max(img.height for img in pil_images)

    # Create a new blank image with white background
    stitched = PILImage.new("RGB", (total_width, max_height), (255, 255, 255))

    # Paste each page image into the stitched image
    x_offset = 0
    for img in pil_images:
        # Calculate vertical offset to center the page if heights differ
        y_offset = (max_height - img.height) // 2
        stitched.paste(img, (x_offset, y_offset))
        x_offset += img.width

    # Convert to PNG bytes
    output = io.BytesIO()
    stitched.save(output, format="PNG")
    result = output.getvalue()

    # Clean up
    for pix in pixmaps:
        pix = None

    return result


def concatenate_page_text(doc: pymupdf.Document, page_indices: list[int]) -> str:
    """
    Concatenate text from multiple pages.

    Args:
        doc: PyMuPDF document
        page_indices: List of 0-based page indices

    Returns:
        Combined text with page separator
    """
    texts = [doc[idx].get_text() for idx in page_indices]
    return "\n\n".join(texts)


def extract_images_from_pages(
    doc: pymupdf.Document,
    page_indices: list[int],
    page_id: str,
    images_dir: str,
    quiet: bool = False,
) -> list[Image]:
    """
    Extract images from multiple pages (for spread mode).

    Args:
        doc: PyMuPDF document
        page_indices: List of 0-based page indices to extract from
        page_id: ID for the spread (e.g., 'p2_3')
        images_dir: Directory to save images
        quiet: Whether to suppress output

    Returns:
        List of Image objects
    """
    images = []
    image_index = 0

    for page_idx in page_indices:
        fitz_page = doc[page_idx]
        page_number = page_idx + 1

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

        # Extract vector drawings
        drawings = fitz_page.get_drawings(extended=True)

        if not quiet:
            print(f"  Page {page_number}: Found {len(drawings)} drawings")
            drawable_count = len([d for d in drawings if d.get("type") not in ["clip", "group"]])
            print(f"  Page {page_number}: Drawable items: {drawable_count}")

        try:
            vector_images = render_drawings(
                drawings,
                page_width=fitz_page.rect.width,
                page_height=fitz_page.rect.height,
                margin_allowance=0,
                overlap_threshold_percent=0.75,
                quiet=quiet,
            )
            if not quiet:
                print(f"  Page {page_number}: Rendered {len(vector_images)} vector images")
        except Exception as e:
            print(f"  ERROR rendering vector images on page {page_number}: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            vector_images = []

        for vector_img in vector_images:
            img_id = f"img_{page_id}_v{image_index}"
            if not quiet:
                print(
                    f"    Vector image {image_index}: {vector_img.width}x{vector_img.height}, {len(vector_img.image)} bytes"
                )

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

    return images


def extract_pages_from_pdf(
    output_dir: str, pdf_path: str, start_page: int, end_page: int, spread_mode: bool = False, quiet: bool = False
) -> PDFExtract:
    """
    Extract pages from PDF file and return structured data.

    Args:
        output_dir: Directory to save extracted images
        pdf_path: Path to the PDF file
        start_page: Starting page number (1-based)
        end_page: Ending page number (1-based, 0 means end of document)
        spread_mode: Whether to extract as spreads (first page solo, then pairs)
        quiet: Whether to suppress progress output

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

    # Capture PDF metadata (Info dictionary and XMP, if present)
    raw_doc_metadata = doc.metadata or {}
    pdf_metadata_dict: dict[str, object] = {}
    for key, value in raw_doc_metadata.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            pdf_metadata_dict[key] = value
        else:
            pdf_metadata_dict[key] = str(value)

    # Determine page range
    total_pages = len(doc)
    end_page = min(end_page, total_pages) if end_page > 0 else total_pages
    start_page = 1 if start_page == 0 else start_page

    # Validate page range
    if start_page < 1 or start_page > total_pages:
        raise ValueError(f"Start page {start_page} is out of range (1-{total_pages})")
    if end_page < start_page:
        raise ValueError(f"End page {end_page} cannot be less than start page {start_page}")

    # Get page groupings based on mode
    page_groupings = get_page_groupings(start_page, end_page, spread_mode)

    pages = []
    extracted_page_numbers = []

    for page_group in page_groupings:
        # Create page ID and track page numbers
        if len(page_group) == 1:
            page_id = f"p{page_group[0]}"
            page_number = page_group[0]
        else:
            page_id = f"p{'_'.join(str(p) for p in page_group)}"
            page_number = page_group[0]  # Use first page number for reference

        extracted_page_numbers.extend(page_group)

        # Convert to 0-based indices
        page_indices = [p - 1 for p in page_group]

        # Extract page image (stitched for spreads)
        if len(page_group) == 1:
            page_image_filename = f"page_{page_group[0]}.png"
        else:
            page_image_filename = f"page_{'_'.join(str(p) for p in page_group)}.png"

        page_image_path = os.path.join(pages_dir, page_image_filename)
        page_image_bytes = stitch_page_images(doc, page_indices)
        write_file(page_image_path, page_image_bytes)

        # Extract text (concatenated for spreads)
        page_text = concatenate_page_text(doc, page_indices)

        # Extract images from all pages in the group
        images = extract_images_from_pages(doc, page_indices, page_id, images_dir, quiet)

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
    extract_metadata = Metadata(
        filename=os.path.basename(pdf_path),
        total_pages=total_pages,
        extracted_pages=extracted_page_numbers,
        extraction_timestamp=datetime.now().isoformat(),
        start_page=start_page,
        end_page=end_page,
        spread_mode=spread_mode,
    )

    # Create final result
    return PDFExtract(extract_metadata=extract_metadata, pdf_metadata=pdf_metadata_dict, pages=pages)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract pages, text, and images from PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all pages in normal mode
  python pdf_extractor.py --pdf_path document.pdf --output_dir ./output
  
  # Extract specific page range
  python pdf_extractor.py --pdf_path doc.pdf --start_page 1 --end_page 5 --output_dir ./output
  
  # Extract as spreads (first page solo, then pairs: 1, 2-3, 4-5, 6-7, etc.)
  python pdf_extractor.py --pdf_path book.pdf --output_dir ./output --spread_mode
  
  # Extract spreads with specific range
  python pdf_extractor.py --pdf_path book.pdf --start_page 1 --end_page 10 --output_dir ./output --spread_mode

Spread Mode:
  When --spread_mode is enabled, pages are extracted as spreads to support books
  meant to be viewed with left and right pages together. Spreads are determined by
  global page numbers, not the extraction range:
    - Page 1 (cover) is always extracted solo
    - Even pages pair with the following odd page: 2-3, 4-5, 6-7, etc.
    - Extracting pages 2-3 results in one spread (p2_3)
    - Extracting pages 3-4 results in two separate pages (p3, p4) since they cross boundaries
    - Extracting pages 4-5 results in one spread (p4_5)
    - Page images are stitched horizontally for spreads
    - Text from both pages is concatenated for spreads
    - Images from both pages are collected with IDs like 'p2_3' for the spread
        """,
    )

    parser.add_argument("--pdf_path", required=True, help="Path to the PDF file to extract")

    parser.add_argument("--output_dir", required=True, help="Directory to save extracted content")

    parser.add_argument("--start_page", type=int, default=1, help="Starting page number (1-based, default: 1)")

    parser.add_argument(
        "--end_page", type=int, default=0, help="Ending page number (1-based, 0 means end of document, default: 0)"
    )

    parser.add_argument(
        "--spread_mode",
        action="store_true",
        help="Extract pages as spreads (first page solo, then pairs of pages combined)",
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
            print(f"Spread mode: {'enabled' if args.spread_mode else 'disabled'}")
            print(f"Output directory: {args.output_dir}")

        # Perform extraction
        result = extract_pages_from_pdf(
            output_dir=args.output_dir,
            pdf_path=args.pdf_path,
            start_page=args.start_page,
            end_page=args.end_page,
            spread_mode=args.spread_mode,
            quiet=args.quiet,
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
