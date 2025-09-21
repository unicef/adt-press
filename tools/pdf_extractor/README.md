# PDF Extractor Tool

A standalone PDF extraction tool that extracts pages, text, and images from PDF files using PyMuPDF.

## License Notice

⚠️ **Important**: This tool uses PyMuPDF, which is licensed under AGPL-3.0.

## Features

- Extract text from PDF pages
- Extract raster images from PDFs
- Extract and render vector drawings
- Generate full-page images
- Create chart visualizations of extracted images
- Output structured JSON with all extraction results
- Organize extracted content in a clean directory structure

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or using the project file
pip install -e .
```

## Usage

### Basic Usage

```bash
python pdf_extractor.py --pdf-path document.pdf --output-dir ./output
```

### Extract Specific Page Range

```bash
python pdf_extractor.py --pdf-path document.pdf --start-page 1 --end-page 5 --output-dir ./output
```

### Command Line Options

- `--pdf-path`: Path to the PDF file to extract (required)
- `--output-dir`: Directory to save extracted content (required)
- `--start-page`: Starting page number (1-based, default: 1)
- `--end-page`: Ending page number (1-based, 0 means end of document, default: 0)
- `--quiet`: Suppress progress output

## Output Structure

The tool creates the following directory structure:

```
output_directory/
├── pdf_extract.json    # Complete extraction metadata
├── pages/
│   ├── page_1.png            # Full page images
│   ├── page_2.png
│   └── ...
└── images/
    ├── img_p1_r0.png         # Raster images
    ├── img_p1_r0_chart.png   # Chart versions
    ├── img_p1_v0.png         # Vector images
    └── ...
```

## JSON Output Format

The `pdf_extract.json` file contains:

```json
{
  "pdf_metadata": {
    "filename": "document.pdf",
    "total_pages": 10,
    "extracted_pages": [1, 2, 3],
    "extraction_timestamp": "2025-09-16T...",
    "start_page": 1,
    "end_page": 3
  },
  "pages": [
    {
      "page_id": "p1",
      "page_number": 1,
      "page_image_path": "pages/page_1.png",
      "text": "extracted text content...",
      "images": [
        {
          "image_id": "img_p1_r0",
          "page_id": "p1",
          "index": 0,
          "image_path": "images/img_p1_r0.png",
          "chart_path": "images/img_p1_r0_chart.png",
          "width": 800,
          "height": 600,
          "image_type": "raster"
        }
      ]
    }
  ]
}
```

## Integration with Other Applications

This tool is designed to be called as a subprocess from other applications to avoid AGPL license propagation:

```python
import subprocess
import json

def extract_pdf_content(pdf_path, start_page, end_page, output_dir):
    cmd = [
        "python", "tools/pdf_extractor/pdf_extractor.py",
        "--pdf-path", pdf_path,
        "--start-page", str(start_page),
        "--end-page", str(end_page),
        "--output-dir", output_dir
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"PDF extraction failed: {result.stderr}")
    
    # Load results
    with open(f"{output_dir}/pdf_extract.json") as f:
        return json.load(f)
```

## Dependencies

- **pymupdf**: PDF processing (AGPL-3.0)
- **matplotlib**: Chart generation (BSD-compatible)
- **pillow**: Image processing (PIL License)
- **pycairo**: Vector graphics rendering (LGPL/MPL)
- **numpy**: Array operations (BSD)
