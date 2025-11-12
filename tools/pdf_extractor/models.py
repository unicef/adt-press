from typing import Any

from pydantic import BaseModel, Field


class Image(BaseModel):
    """Represents an extracted image from a PDF page."""

    image_id: str
    page_id: str
    index: int
    image_path: str  # Relative path within output directory
    chart_path: str  # Relative path to chart version
    width: int
    height: int
    image_type: str  # "raster" or "vector"


class Page(BaseModel):
    """Represents an extracted PDF page.

    In spread mode, a Page may represent multiple physical pages combined:
    - page_id: Single page uses 'p1', 'p2', etc. Spreads use 'p2_3', 'p4_5', etc.
    - page_number: References the first page number in the spread
    - page_image_path: For spreads, contains horizontally stitched image
    - text: For spreads, contains concatenated text from all pages
    - images: For spreads, contains images from all pages in the spread
    """

    page_id: str
    page_number: int
    page_image_path: str  # Relative path to full page image
    text: str
    images: list[Image]


class Metadata(BaseModel):
    """Metadata about the extracted PDF.

    The spread_mode field indicates whether pages were extracted as spreads.
    When True, spreads follow global page numbering: page 1 is solo (cover),
    then even pages pair with following odd pages (2-3, 4-5, 6-7, etc.).
    """

    filename: str
    total_pages: int
    extracted_pages: list[int]
    extraction_timestamp: str
    start_page: int
    end_page: int
    spread_mode: bool = False


class PDFExtract(BaseModel):
    """Complete PDF extraction result."""

    extract_metadata: Metadata
    pdf_metadata: dict[str, Any] = Field(default_factory=dict)
    pages: list[Page]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json(indent=2)

    def save_to_file(self, filepath: str) -> None:
        """Save extraction result to JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_json())
