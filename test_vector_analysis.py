#!/usr/bin/env python3
"""
Test script to analyze vector element classification and grouping behavior.
"""

import tempfile
import fitz
from adt_press.utils.image import extract_vector_groups, _is_large_background_element, _is_likely_text_element, _estimate_drawing_complexity, _compute_drawing_bbox

def analyze_vector_elements():
    """Analyze how vector elements are being classified."""
    pdf_path = "assets/cuaderno3.pdf"  # This one has illustrations
    
    # Open PDF directly to analyze
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]  # Analyze first page
    
    print("Vector Element Analysis")
    print("="*50)
    
    drawings = page.get_drawings()
    print(f"Total vector drawings: {len(drawings)}")
    
    # Analyze each drawing
    text_count = 0
    background_count = 0
    illustration_count = 0
    low_complexity_count = 0
    
    for i, drawing in enumerate(drawings[:20]):  # Analyze first 20 for brevity
        bbox = _compute_drawing_bbox(drawing)
        is_text = _is_likely_text_element(drawing, bbox)
        is_background = _is_large_background_element(bbox, page)
        complexity = _estimate_drawing_complexity(drawing)
        
        if is_text:
            text_count += 1
        elif is_background:
            background_count += 1
        elif complexity <= 2:
            low_complexity_count += 1
        else:
            illustration_count += 1
        
        if i < 10:  # Show details for first 10
            print(f"Drawing {i:2d}: {bbox.width:5.1f}x{bbox.height:5.1f} pts, "
                  f"complexity={complexity:2d}, "
                  f"text={is_text}, background={is_background}")
    
    print(f"\nClassification Summary (first 20 drawings):")
    print(f"  Text elements: {text_count}")
    print(f"  Background elements: {background_count}")
    print(f"  Low complexity: {low_complexity_count}")
    print(f"  Illustration elements: {illustration_count}")
    
    # Test grouping
    print(f"\nGrouping Analysis:")
    with tempfile.TemporaryDirectory() as temp_dir:
        from adt_press.utils.pdf import pages_for_pdf
        pages = pages_for_pdf(temp_dir, pdf_path, start_page=0, end_page=1)
        page_data = pages[0]
        
        vector_images = [img for img in page_data.images if 'v' in img.image_id]
        print(f"Vector images created: {len(vector_images)}")
        
        composite_images = [img for img in vector_images if img.is_composite]
        single_images = [img for img in vector_images if not img.is_composite]
        
        print(f"Composite images: {len(composite_images)}")
        print(f"Single element images: {len(single_images)}")
        
        if composite_images:
            component_counts = [img.component_count for img in composite_images]
            print(f"Components per composite: min={min(component_counts)}, max={max(component_counts)}, avg={sum(component_counts)/len(component_counts):.1f}")

if __name__ == "__main__":
    analyze_vector_elements()
