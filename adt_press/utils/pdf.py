import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from adt_press.models.image import Image
from adt_press.models.pdf import Page


def _copy_image(extract_dir: str, images_dir: str, relative_path: str) -> str:
    """
    Copy an image file from extract directory to images directory.
    
    Args:
        extract_dir: Source directory containing the original file
        images_dir: Destination directory for copied files
        relative_path: Relative path of the file within extract_dir
    
    Returns:
        Path relative to current working directory
    """
    original_path = os.path.join(extract_dir, relative_path)
    filename = os.path.basename(relative_path)
    new_path = os.path.join(images_dir, filename)
    
    if os.path.exists(original_path):
        shutil.copy2(original_path, new_path)
    
    # Return path relative to current working directory
    return os.path.relpath(new_path)


def pages_for_pdf(output_dir: str, pdf_path: str, start_page: int, end_page: int) -> list[Page]:
    """
    Extract pages from PDF using the standalone pdf_extractor tool.
    
    Args:
        output_dir: Directory to save extracted content
        pdf_path: Path to the PDF file
        start_page: Starting page number (1-based)
        end_page: Ending page number (1-based, 0 means end of document)
    
    Returns:
        List of Page objects with extracted content
    """
    # Create extract subdirectory, save as absolute path
    extract_dir = os.path.join(output_dir, "extract")
    os.makedirs(extract_dir, exist_ok=True)
    
    # Create images directory for copying images
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    # Get the path to the pdf_extractor script
    current_file = Path(__file__)
    repo_root = current_file.parent.parent.parent  # Go up from adt_press/utils/pdf.py to repo root
    extractor_script = repo_root / "tools" / "pdf_extractor" / "pdf_extractor.py"
    
    # Build the command
    cmd = [
        sys.executable,  # Use the same Python interpreter
        str(extractor_script),
        "--pdf_path", pdf_path,
        "--output_dir", extract_dir,
        "--start_page", str(start_page),
        "--end_page", str(end_page),
        "--quiet"  # Suppress output for cleaner logs
    ]
    
    # Run the extractor
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"PDF extraction failed: {e.stderr}") from e
    
    # Parse the results
    results_file = os.path.join(extract_dir, "pdf_extract.json")
    if not os.path.exists(results_file):
        raise RuntimeError(f"Extraction results file not found: {results_file}")
    
    with open(results_file, 'r') as f:
        extract_data = json.load(f)
    
    # Convert to our models and copy images to images directory
    pages = []
    for page_data in extract_data["pages"]:
        # Convert images and copy them to images directory
        images = []
        for img_data in page_data["images"]:
            image = Image(
                image_id=img_data["image_id"],
                page_id=img_data["page_id"],
                index=img_data["index"],
                image_path=_copy_image(extract_dir, images_dir, img_data["image_path"]),
                chart_path=_copy_image(extract_dir, images_dir, img_data["chart_path"]),
                width=img_data["width"],
                height=img_data["height"],
                image_type=img_data["image_type"]
            )
            images.append(image)
        
        # Create page object with copied image path
        page = Page(
            page_id=page_data["page_id"],
            page_number=page_data["page_number"],
            page_image_path=_copy_image(extract_dir, images_dir, page_data["page_image_path"]),
            text=page_data["text"],
            images=images
        )
        pages.append(page)
    
    return pages
