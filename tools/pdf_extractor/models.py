from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import json


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
    """Represents an extracted PDF page."""
    page_id: str
    page_number: int
    page_image_path: str  # Relative path to full page image
    text: str
    images: List[Image]


class Metadata(BaseModel):
    """Metadata about the extracted PDF."""
    filename: str
    total_pages: int
    extracted_pages: List[int]
    extraction_timestamp: str
    start_page: int
    end_page: int


class PDFExtract(BaseModel):
    """Complete PDF extraction result."""
    pdf_metadata: Metadata
    pages: List[Page]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump()
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json(indent=2)
    
    def save_to_file(self, filepath: str) -> None:
        """Save extraction result to JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())
