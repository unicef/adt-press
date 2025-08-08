#!/usr/bin/env python3
"""
Test script to demonstrate the improvement in size filtering with vector grouping.
"""

import tempfile
from adt_press.utils.pdf import pages_for_pdf
from adt_press.nodes.config_nodes import ImageSizeFilterConfig
from adt_press.nodes.image_nodes import image_size_filter_failures

def test_size_filtering_improvement():
    """Demonstrate how vector grouping improves size filtering."""
    pdf_path = "assets/cuaderno3.pdf"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Testing size filtering with enhanced vector grouping...")
        print("="*60)
        
        # Process first page
        pages = pages_for_pdf(temp_dir, pdf_path, start_page=0, end_page=1)
        page = pages[0]
        
        print(f"Page {page.page_number}:")
        print(f"  Total images extracted: {len(page.images)}")
        
        # Configure size filter (typical values)
        size_filter_config = ImageSizeFilterConfig(
            min_side=50,  # 50 points minimum (about 0.7 inches)
            max_side=2000  # 2000 points maximum
        )
        
        # Apply size filter
        filter_failures = image_size_filter_failures(page.images, size_filter_config)
        
        print(f"  Images that would be filtered out: {len(filter_failures)}")
        print(f"  Images that pass filter: {len(page.images) - len(filter_failures)}")
        
        print("\nImage Details:")
        for img in page.images:
            status = "FILTERED" if img.image_id in filter_failures else "KEPT"
            composite_info = f" (composite: {img.component_count} components)" if img.is_composite else ""
            print(f"  {img.image_id}: {img.width_points:.1f}x{img.height_points:.1f} pts - {status}{composite_info}")
            
        print("\nComposite Image Benefits:")
        composite_images = [img for img in page.images if img.is_composite]
        if composite_images:
            for img in composite_images:
                print(f"  {img.image_id}: Grouped {img.component_count} vector elements")
                print(f"    Final size: {img.width_points:.1f}x{img.height_points:.1f} pts")
                print(f"    Would individual elements survive filtering? Probably not - many would be <50pts")
                print(f"    Does composite survive filtering? {'YES' if img.image_id not in filter_failures else 'NO'}")
        else:
            print("  No composite images found on this page")

if __name__ == "__main__":
    test_size_filtering_improvement()
