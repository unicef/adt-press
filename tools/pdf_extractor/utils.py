"""
Utility functions for the PDF extractor tool.
These are copied and adapted from the main application utilities.
"""

import io
import warnings

import cairo
import matplotlib.pyplot as plt
import numpy as np
import PIL.Image
import math

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


def convert_color_cairo(color: list[float]) -> tuple:
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
        elif cmd == "qu":
            # Quadrilateral - check all 4 points
            quad = item[1]
            for point in quad:
                if hasattr(point, "x") and hasattr(point, "y"):
                    min_x = min(min_x, point.x)
                    min_y = min(min_y, point.y)
                    max_x = max(max_x, point.x)
                    max_y = max(max_y, point.y)
        elif cmd in ["m", "l", "c", "v"]:
            # Move, line, cubic curve, or quadratic curve - check all points
            points = item[1:]
            for point in points:
                if hasattr(point, "x") and hasattr(point, "y"):
                    min_x = min(min_x, point.x)
                    min_y = min(min_y, point.y)
                    max_x = max(max_x, point.x)
                    max_y = max(max_y, point.y)

    return (min_x, min_y, max_x, max_y)


def boxes_overlap(
    box1: tuple[float, float, float, float], box2: tuple[float, float, float, float], margin_allowance: int, overlap_threshold: int
) -> bool:  # pragma: no cover
    """Check if two bounding boxes overlap."""
    min_x1, min_y1, max_x1, max_y1 = box1
    min_x2, min_y2, max_x2, max_y2 = box2
    # if one of the boxes is larger than 800 px, we consider it as a full page and return no.
    if max_x1 - min_x1 > overlap_threshold or max_x2 - min_x2 > overlap_threshold:
        return False
    if max_y1 - min_y1 > overlap_threshold or max_y2 - min_y2 > overlap_threshold:
        return False
    return not (
        max_x1 + margin_allowance < min_x2
        or max_x2 + margin_allowance < min_x1
        or max_y1 + margin_allowance < min_y2
        or max_y2 + margin_allowance < min_y1
    )


def group_overlapping_drawings(drawings, margin_allowance: int, overlap_threshold: int):  # pragma: no cover
    """Group drawings that overlap based on their bounding boxes."""
    bounding_boxes = [compute_bounding_box(drawing) for drawing in drawings]
    n = len(drawings)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # Path compression
            x = parent[x]
        return x

    def union(x, y):
        x_root = find(x)
        y_root = find(y)
        if x_root != y_root:
            parent[y_root] = x_root

    # Union drawings with overlapping bounding boxes
    for i in range(n):
        for j in range(i + 1, n):
            if boxes_overlap(bounding_boxes[i], bounding_boxes[j], margin_allowance, overlap_threshold):
                union(i, j)

    # Group drawings based on their root parent
    groups: dict[int, list] = {}
    for i in range(n):
        root = find(i)
        if root not in groups:
            groups[root] = []
        # Store seqno (if available) or index for z-order preservation
        seqno = drawings[i].get('seqno', i)
        groups[root].append((seqno, drawings[i]))

    # Sort each group by seqno to maintain z-order within the group
    # Then sort groups by their minimum seqno to maintain z-order between groups
    sorted_groups = []
    for group_items in groups.values():
        group_items.sort(key=lambda x: x[0])  # Sort by seqno
        min_seqno = group_items[0][0]  # Get minimum seqno for this group
        sorted_groups.append((min_seqno, [item[1] for item in group_items]))
    
    # Sort groups by their minimum seqno
    sorted_groups.sort(key=lambda x: x[0])
    
    return [group[1] for group in sorted_groups]  # Extract just the drawings


def parse_items_and_draw_cairo(ctx, items):  # pragma: no cover
    """Parse the drawing items and draw on the Cairo context."""
    for item in items:
        cmd = item[0]
        if cmd == "m":  # Move to
            p = item[1]
            ctx.move_to(p.x, p.y)
        elif cmd == "l":  # Line to
            # PyMuPDF 'l' command has [cmd, start_point, end_point]
            if len(item) == 3:
                start_p, end_p = item[1], item[2]
                # Ensure we're at the start point
                ctx.line_to(start_p.x, start_p.y)
                ctx.line_to(end_p.x, end_p.y)
            else:
                # Fallback for single point
                p = item[1]
                ctx.line_to(p.x, p.y)
        elif cmd == "c":  # Cubic Bezier curve
            # PyMuPDF 'c' command has [cmd, start_point, cp1, cp2, end_point]
            if len(item) == 5:
                start_p, cp1, cp2, end_p = item[1], item[2], item[3], item[4]
                # Ensure we're at the start point (curve_to draws from current point)
                ctx.line_to(start_p.x, start_p.y)
                ctx.curve_to(cp1.x, cp1.y, cp2.x, cp2.y, end_p.x, end_p.y)
            else:
                # Fallback for different structure (3 points: 2 control + 1 end)
                p1, p2, p3 = item[1], item[2], item[3]
                ctx.curve_to(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)
        elif cmd == "v":  # Quadratic Bezier curve (v command)
            # PyMuPDF quadratic curve: control point + end point
            # Cairo doesn't have native quadratic curves, so convert to cubic
            # Get current point
            current_x, current_y = ctx.get_current_point()
            p1, p2 = item[1], item[2]  # control point, end point
            # Convert quadratic to cubic Bezier
            # Cubic control points are at 2/3 from start/end toward quadratic control
            cp1_x = current_x + 2.0/3.0 * (p1.x - current_x)
            cp1_y = current_y + 2.0/3.0 * (p1.y - current_y)
            cp2_x = p2.x + 2.0/3.0 * (p1.x - p2.x)
            cp2_y = p2.y + 2.0/3.0 * (p1.y - p2.y)
            ctx.curve_to(cp1_x, cp1_y, cp2_x, cp2_y, p2.x, p2.y)
        elif cmd == "h":  # Close path
            ctx.close_path()
        elif cmd == "re":  # Rectangle
            rect = item[1]
            ctx.rectangle(rect.x0, rect.y0, rect.x1 - rect.x0, rect.y1 - rect.y0)
        elif cmd == "qu":
            quad = item[1]
            # p1 is bottom-right, we go in clockwise.
            p1, p2, p3, p4 = quad[0], quad[1], quad[3], quad[2]
            ctx.move_to(p1.x, p1.y)
            ctx.line_to(p2.x, p2.y)
            ctx.line_to(p3.x, p3.y)
            ctx.line_to(p4.x, p4.y)
            ctx.close_path()


def render_group_to_image(group_drawings) -> RenderedVectorImage:
    # Compute the overall bounding box for the group
    bounding_boxes = [compute_bounding_box(d) for d in group_drawings]
    min_x = min(box[0] for box in bounding_boxes)
    min_y = min(box[1] for box in bounding_boxes)
    max_x = max(box[2] for box in bounding_boxes)
    max_y = max(box[3] for box in bounding_boxes)
    
    # Sanity check: if bounding box is too large, something is wrong
    # Typical PDF page is ~600x800 points, so anything over 10000 is suspicious
    bbox_width = max_x - min_x
    bbox_height = max_y - min_y
    if bbox_width > 10000 or bbox_height > 10000 or bbox_width <= 0 or bbox_height <= 0:
        # Return a minimal empty image
        return RenderedVectorImage(image=b'', width=0, height=0)

    # Scale factor: PDF points are 72 DPI, scale to 150 DPI
    scale = 150.0 / 72.0
    
    width = int(math.ceil(bbox_width * scale))
    height = int(math.ceil(bbox_height * scale))

    # Ensure minimum dimensions
    if width <= 0:
        width = 10
    if height <= 0:
        height = 10
    
    # Cairo has a maximum surface size (typically 32767x32767)
    # If dimensions are too large, scale down
    MAX_DIMENSION = 32000
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        scale_down = min(MAX_DIMENSION / width, MAX_DIMENSION / height)
        width = int(width * scale_down)
        height = int(height * scale_down)
        scale = scale * scale_down

    # Create a Cairo surface and context for the group
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    # Set tolerance for curve rendering (lower = smoother curves, matches PyMuPDF better)
    ctx.set_tolerance(0.1)

    # Clear the surface to fully transparent
    ctx.set_source_rgba(0, 0, 0, 0)  # Transparent
    ctx.set_operator(cairo.OPERATOR_SOURCE)  # Replace everything (including alpha)
    ctx.paint()
    ctx.set_operator(cairo.OPERATOR_OVER)  # Reset to normal compositing

    # Apply scaling and translation
    ctx.scale(scale, scale)
    ctx.translate(-min_x, -min_y)

    # Draw each drawing in the group
    for drawing in group_drawings:
        # Handle filling and stroking based on the drawing type
        drawing_type = drawing.get("type", "")
        
        # Set fill rule BEFORE creating the path (always use winding to match PyMuPDF)
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        
        ctx.new_path()  # Start a new path for each drawing
        parse_items_and_draw_cairo(ctx, drawing["items"])

        has_fill = "f" in drawing_type
        has_stroke = "s" in drawing_type
        
        if has_fill:  # Filled Path
            fill_color = convert_color_cairo(drawing.get("fill")) if drawing.get("fill") else (0, 0, 0)
            fill_opacity = drawing.get("fill_opacity", 1.0)
            ctx.set_source_rgba(*fill_color, fill_opacity)
            if has_stroke:
                ctx.fill_preserve()  # Preserve the path for stroking
            else:
                ctx.fill()  # Consume the path since there's no stroke

        if has_stroke:  # Stroked Path
            stroke_color = convert_color_cairo(drawing.get("color")) if drawing.get("color") else (0, 0, 0)
            stroke_width = drawing.get("width", 1)
            stroke_opacity = drawing.get("stroke_opacity", 1.0)
            ctx.set_source_rgba(*stroke_color, stroke_opacity)
            ctx.set_line_width(stroke_width)
            ctx.stroke()

    # Get the final image width and height.
    width, height = surface.get_width(), surface.get_height()

    # write our PNG
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


def render_drawings(drawings, margin_allowance: int, overlap_threshold: int) -> list[RenderedVectorImage]:
    """Renders the passed in PDF drawings to images, grouping overlapping drawings."""
    groups = group_overlapping_drawings(drawings, margin_allowance, overlap_threshold)
    results = [render_group_to_image(group) for group in groups]
    return [r for r in results if r.width > 0 and r.height > 0]  # Filter out empty images
