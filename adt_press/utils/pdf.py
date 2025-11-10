import os
import subprocess
import sys
from pathlib import Path


def extract_pdf_to_dir(output_dir: str, pdf_path: str, start_page: int, end_page: int, spread_mode: bool = False) -> str:
    """
    Extract pages from PDF using the standalone pdf_extractor tool.

    Args:
        output_dir: Directory to save extracted content
        pdf_path: Path to the PDF file
        start_page: Starting page number (1-based)
        end_page: Ending page number (1-based, 0 means end of document)
        spread_mode: Whether to extract as spreads (first page solo, then pairs)

    Returns:
        Path to the extraction directory containing pdf_extract.json
    """
    # Create extract subdirectory, save as absolute path
    extract_dir = os.path.join(output_dir, "extract")
    os.makedirs(extract_dir, exist_ok=True)

    # Get the path to the pdf_extractor script
    current_file = Path(__file__)
    repo_root = current_file.parent.parent.parent  # Go up from adt_press/utils/pdf.py to repo root
    extractor_script = repo_root / "tools" / "pdf_extractor" / "pdf_extractor.py"

    # Build the command
    cmd = [
        sys.executable,  # Use the same Python interpreter
        str(extractor_script),
        "--pdf_path",
        pdf_path,
        "--output_dir",
        extract_dir,
        "--start_page",
        str(start_page),
        "--end_page",
        str(end_page),
        "--quiet",
    ]

    # Add spread mode flag if enabled
    if spread_mode:
        cmd.append("--spread_mode")

    # Run the extractor
    try:
        subprocess.run(cmd, check=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"PDF extraction failed with exit code {e.returncode}") from e

    # Return the extraction directory
    return extract_dir
