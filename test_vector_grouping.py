#!/usr/bin/env python3
"""
Simple test script to verify the enhanced vector grouping functionality.
"""

import tempfile
import os
import fitz
from adt_press.utils.pdf import pages_for_pdf

def test_vector_grouping():
    """Test the enhanced vector grouping on a PDF."""
    pdf_path = "assets/cuaderno3.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file {pdf_path} not found")
        return
    
    # First, let's check what vector drawings exist
    print("Checking for vector drawings in PDF...")
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page_num in range(min(3, len(doc))):  # Check first 3 pages
        page = doc[page_num]
        drawings = page.get_drawings()
        print(f"Page {page_num + 1}: {len(drawings)} vector drawings")
        
        if drawings:
            for i, drawing in enumerate(drawings[:3]):  # Show first 3 drawings
                print(f"  Drawing {i}: {len(drawing.get('items', []))} items")
    
    # Create temporary output directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Processing PDF: {pdf_path}")
        print(f"Output directory: {temp_dir}")
        
        try:
            # Process first few pages to find one with vector graphics
            pages = pages_for_pdf(temp_dir, pdf_path, start_page=0, end_page=2)  # Try first 2 pages
            
            print(f"Processed {len(pages)} page(s)")
            
            for page in pages:
                print(f"\nPage {page.page_number} ({page.page_id}):")
                print(f"  Total images: {len(page.images)}")
                
                # Count different types of images
                raster_count = len([img for img in page.images if 'r' in img.image_id])
                vector_count = len([img for img in page.images if 'v' in img.image_id])
                composite_count = len([img for img in page.images if img.is_composite])
                
                print(f"  Raster images: {raster_count}")
                print(f"  Vector images: {vector_count}")
                print(f"  Composite images: {composite_count}")
                
                # Show details for each image
                for img in page.images:
                    print(f"    {img.image_id}: {img.width_points:.1f}x{img.height_points:.1f} pts")
                    if img.is_composite:
                        print(f"      Composite with {img.component_count} components")
                    if img.bbox_points:
                        x0, y0, x1, y1 = img.bbox_points
                        print(f"      BBox: ({x0:.1f}, {y0:.1f}) to ({x1:.1f}, {y1:.1f})")
                        
        except Exception as e:
            print(f"Error during processing: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_vector_grouping()
