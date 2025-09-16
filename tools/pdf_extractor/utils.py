"""
Utility functions for the PDF extractor tool.
These are copied and adapted from the main application utilities.
"""
import io
import os
import warnings
from typing import List

import cairo
import matplotlib.pyplot as plt
import numpy as np
import PIL.Image

from models import Image

# Configure matplotlib for headless operation
plt.switch_backend("Agg")
warnings.filterwarnings("ignore", category=RuntimeWarning)
plt.rcParams.update({"figure.max_open_warning": 100})


def write_file(output_path: str, data: bytes, suffix: str = "") -> str:
    """Writes bytes to the specified output path, optionally appending a suffix to the filename."""
    
    # if we have a suffix, add it in after removing the extension
    if suffix != "":
        output_path = output_path.rsplit(".", 1)[0] + f"_{suffix}." + output_path.rsplit(".", 1)[1]

    with open(output_path, "wb") as f:
        f.write(data)

    return output_path


def matplotlib_chart(img_bytes: bytes) -> bytes:
    """Generates a matplotlib chart from the image bytes and returns it as PNG bytes."""
    
    image = PIL.Image.open(io.BytesIO(img_bytes))
    fig, ax = plt.subplots(figsize=(10, 6), dpi=200)

    ax.imshow(image)

    # Increase the density of coordinates on the axes
    x_ticks = ax.get_xticks()
    y_ticks = ax.get_yticks()
    ax.set_xticks(np.linspace(x_ticks[0], x_ticks[-1], len(x_ticks) * 2 - 1))
    ax.set_yticks(np.linspace(y_ticks[0], y_ticks[-1], len(y_ticks) * 2 - 1))
    plt.xticks(rotation=45)

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close(fig)
    buffer.seek(0)
    return buffer.getvalue()


class RenderedVectorImage:
    """Simple class to hold rendered vector image data."""
    def __init__(self, image: bytes, width: int, height: int):
        self.image = image
        self.width = width
        self.height = height


def convert_color_cairo(color: List[float]) -> tuple:
    """Convert a float-based color to a Cairo color with a default."""
    return tuple(c for c in color) if color else (0, 0, 0)


def compute_bounding_box(drawing) -> tuple:
    """Compute the bounding box of a drawing."""
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    for item in drawing["items"]:
        cmd = item[0]

        if cmd == "re":
            rect = item[1]
            min_x = min(min_x, rect.x0, rect.x1)
            min_y = min(min_y, rect.y0, rect.y1)
            max_x = max(max_x, rect.x0, rect.x1)
            max_y = max(max_y, rect.y0, rect.y1)
        elif cmd in ["m", "l", "c"]:
            points = item[1:]
            for point in points:
                if hasattr(point, 'x') and hasattr(point, 'y'):
                    min_x = min(min_x, point.x)
                    min_y = min(min_y, point.y)
                    max_x = max(max_x, point.x)
                    max_y = max(max_y, point.y)

    return (min_x, min_y, max_x, max_y)


def group_overlapping_drawings(drawings, margin_allowance: int, overlap_threshold: int) -> List[List]:
    """Group drawings that overlap within threshold."""
    if not drawings:
        return []
    
    # Simple grouping logic - for now, group all drawings together
    # This can be enhanced with actual overlap detection
    return [drawings] if drawings else []


def render_group_to_image(group) -> RenderedVectorImage:
    """Render a group of drawings to a single image."""
    if not group:
        return RenderedVectorImage(b"", 0, 0)
    
    # Compute overall bounding box
    overall_min_x = overall_min_y = float("inf")
    overall_max_x = overall_max_y = float("-inf")
    
    for drawing in group:
        min_x, min_y, max_x, max_y = compute_bounding_box(drawing)
        overall_min_x = min(overall_min_x, min_x)
        overall_min_y = min(overall_min_y, min_y)
        overall_max_x = max(overall_max_x, max_x)
        overall_max_y = max(overall_max_y, max_y)
    
    # Create surface with padding
    padding = 10
    width = int(overall_max_x - overall_min_x + 2 * padding)
    height = int(overall_max_y - overall_min_y + 2 * padding)
    
    if width <= 0 or height <= 0:
        return RenderedVectorImage(b"", 0, 0)
    
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)
    
    # Set white background
    ctx.set_source_rgb(1, 1, 1)
    ctx.paint()
    
    # Translate to account for padding and bounding box offset
    ctx.translate(padding - overall_min_x, padding - overall_min_y)
    
    # Render each drawing
    for drawing in group:
        render_single_drawing(ctx, drawing)
    
    # Convert to PNG bytes
    buffer = io.BytesIO()
    surface.write_to_png(buffer)
    buffer.seek(0)
    
    return RenderedVectorImage(image=buffer.getvalue(), width=width, height=height)


def render_single_drawing(ctx: cairo.Context, drawing):
    """Render a single drawing to the Cairo context."""
    # Simplified rendering - this would need full implementation
    # based on the original vector.py logic
    try:
        for item in drawing.get("items", []):
            cmd = item[0]
            
            if cmd == "re":  # Rectangle
                rect = item[1]
                ctx.rectangle(rect.x0, rect.y0, rect.x1 - rect.x0, rect.y1 - rect.y0)
            elif cmd == "m":  # Move to
                point = item[1]
                ctx.move_to(point.x, point.y)
            elif cmd == "l":  # Line to
                point = item[1]
                ctx.line_to(point.x, point.y)
            # Add more drawing commands as needed
        
        # Apply stroke/fill
        drawing_type = drawing.get("type", "")
        if "f" in drawing_type:  # Fill
            fill_color = convert_color_cairo(drawing.get("fill", [0, 0, 0]))
            ctx.set_source_rgb(*fill_color)
            ctx.fill_preserve()
        
        if "s" in drawing_type:  # Stroke
            stroke_color = convert_color_cairo(drawing.get("color", [0, 0, 0]))
            stroke_width = drawing.get("width", 1)
            ctx.set_source_rgb(*stroke_color)
            ctx.set_line_width(stroke_width)
            ctx.stroke()
            
    except Exception:
        # If rendering fails, just skip this drawing
        pass


def render_drawings(drawings, margin_allowance: int, overlap_threshold: int) -> List[RenderedVectorImage]:
    """Renders the passed in PDF drawings to images, grouping overlapping drawings."""
    groups = group_overlapping_drawings(drawings, margin_allowance, overlap_threshold)
    results = [render_group_to_image(group) for group in groups]
    return [r for r in results if r.width > 0 and r.height > 0]  # Filter out empty images
