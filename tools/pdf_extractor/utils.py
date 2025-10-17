"""
Utility functions for the PDF extractor tool.
These are copied and adapted from the main application utilities.
"""

import io
import math
import warnings

import cairo
import matplotlib.pyplot as plt
import numpy as np
import PIL.Image

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
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)

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


def _cubic_bezier_bounds(p0, p1, p2, p3, coord_attr):
    """Calculate the min/max of a cubic Bezier curve for a given coordinate (x or y).

    A cubic Bezier is defined as: B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3
    The extrema occur at t=0, t=1, or where the derivative = 0.
    Derivative: B'(t) = 3(1-t)²(P1-P0) + 6(1-t)t(P2-P1) + 3t²(P3-P2)
    Setting to 0 and solving gives us a quadratic equation: at² + bt + c = 0
    """
    # Get the coordinate values (x or y)
    c0 = getattr(p0, coord_attr)
    c1 = getattr(p1, coord_attr)
    c2 = getattr(p2, coord_attr)
    c3 = getattr(p3, coord_attr)

    # Start with endpoints
    bounds = [c0, c3]

    # Coefficients for the derivative quadratic equation
    a = 3 * (-c0 + 3 * c1 - 3 * c2 + c3)
    b = 6 * (c0 - 2 * c1 + c2)
    c = 3 * (c1 - c0)

    # Solve quadratic equation at² + bt + c = 0
    if abs(a) > 1e-10:  # Not a degenerate case
        discriminant = b * b - 4 * a * c
        if discriminant >= 0:
            sqrt_disc = math.sqrt(discriminant)
            t1 = (-b + sqrt_disc) / (2 * a)
            t2 = (-b - sqrt_disc) / (2 * a)

            # Check if t values are in valid range [0, 1]
            for t in [t1, t2]:
                if 0 < t < 1:
                    # Evaluate Bezier at this t
                    s = 1 - t
                    val = s * s * s * c0 + 3 * s * s * t * c1 + 3 * s * t * t * c2 + t * t * t * c3
                    bounds.append(val)
    elif abs(b) > 1e-10:  # Linear case
        t = -c / b
        if 0 < t < 1:
            s = 1 - t
            val = s * s * s * c0 + 3 * s * s * t * c1 + 3 * s * t * t * c2 + t * t * t * c3
            bounds.append(val)

    return min(bounds), max(bounds)


def _quadratic_bezier_bounds(p0, p1, p2, coord_attr):
    """Calculate the min/max of a quadratic Bezier curve for a given coordinate.

    Quadratic Bezier: B(t) = (1-t)²P0 + 2(1-t)tP1 + t²P2
    Derivative: B'(t) = 2(1-t)(P1-P0) + 2t(P2-P1)
    Setting to 0: t = (P0-P1)/(P0-2P1+P2)
    """
    c0 = getattr(p0, coord_attr)
    c1 = getattr(p1, coord_attr)
    c2 = getattr(p2, coord_attr)

    bounds = [c0, c2]

    denominator = c0 - 2 * c1 + c2
    if abs(denominator) > 1e-10:
        t = (c0 - c1) / denominator
        if 0 < t < 1:
            # Evaluate Bezier at this t
            s = 1 - t
            val = s * s * c0 + 2 * s * t * c1 + t * t * c2
            bounds.append(val)

    return min(bounds), max(bounds)


def compute_bounding_box(drawing) -> tuple:
    """Compute the accurate bounding box of a drawing.

    For curves, this calculates the actual mathematical bounds, not just the
    control points, which prevents false overlaps from control points that
    extend beyond the visible curve.
    """
    # Skip group elements (from extended=True mode) - they don't have items
    if drawing.get("type") == "group" or "items" not in drawing:
        # Use rect if available, otherwise return empty bounds
        rect = drawing.get("rect")
        if rect:
            return (rect.x0, rect.y0, rect.x1, rect.y1)
        return (0, 0, 0, 0)

    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    # Track current position for curves that draw from current point
    current_x = current_y = 0.0

    for item in drawing["items"]:
        cmd = item[0]

        if cmd == "m":  # Move
            p = item[1]
            current_x, current_y = p.x, p.y
            min_x = min(min_x, p.x)
            min_y = min(min_y, p.y)
            max_x = max(max_x, p.x)
            max_y = max(max_y, p.y)

        elif cmd == "l":  # Line
            if len(item) == 3:
                start_p, end_p = item[1], item[2]
                current_x, current_y = end_p.x, end_p.y
                min_x = min(min_x, start_p.x, end_p.x)
                min_y = min(min_y, start_p.y, end_p.y)
                max_x = max(max_x, start_p.x, end_p.x)
                max_y = max(max_y, start_p.y, end_p.y)
            else:
                p = item[1]
                current_x, current_y = p.x, p.y
                min_x = min(min_x, p.x)
                min_y = min(min_y, p.y)
                max_x = max(max_x, p.x)
                max_y = max(max_y, p.y)

        elif cmd == "c":  # Cubic Bezier
            if len(item) == 5:
                start_p, cp1, cp2, end_p = item[1], item[2], item[3], item[4]
                # Calculate actual curve bounds
                x_min, x_max = _cubic_bezier_bounds(start_p, cp1, cp2, end_p, "x")
                y_min, y_max = _cubic_bezier_bounds(start_p, cp1, cp2, end_p, "y")
                min_x = min(min_x, x_min)
                max_x = max(max_x, x_max)
                min_y = min(min_y, y_min)
                max_y = max(max_y, y_max)
                current_x, current_y = end_p.x, end_p.y
            else:
                # Fallback for different structure
                for point in item[1:]:
                    if hasattr(point, "x"):
                        min_x = min(min_x, point.x)
                        max_x = max(max_x, point.x)
                        min_y = min(min_y, point.y)
                        max_y = max(max_y, point.y)

        elif cmd == "v":  # Quadratic Bezier
            if len(item) == 3:
                p0_x, p0_y = current_x, current_y
                cp, end_p = item[1], item[2]

                # Create Point-like objects for the calculation
                class P:
                    def __init__(self, x, y):
                        self.x = x
                        self.y = y

                p0 = P(p0_x, p0_y)
                x_min, x_max = _quadratic_bezier_bounds(p0, cp, end_p, "x")
                y_min, y_max = _quadratic_bezier_bounds(p0, cp, end_p, "y")
                min_x = min(min_x, x_min)
                max_x = max(max_x, x_max)
                min_y = min(min_y, y_min)
                max_y = max(max_y, y_max)
                current_x, current_y = end_p.x, end_p.y
            else:
                for point in item[1:]:
                    if hasattr(point, "x"):
                        min_x = min(min_x, point.x)
                        max_x = max(max_x, point.x)
                        min_y = min(min_y, point.y)
                        max_y = max(max_y, point.y)

        elif cmd == "re":  # Rectangle
            rect = item[1]
            min_x = min(min_x, rect.x0, rect.x1)
            min_y = min(min_y, rect.y0, rect.y1)
            max_x = max(max_x, rect.x0, rect.x1)
            max_y = max(max_y, rect.y0, rect.y1)

        elif cmd == "qu":  # Quadrilateral
            quad = item[1]
            for point in quad:
                if hasattr(point, "x") and hasattr(point, "y"):
                    min_x = min(min_x, point.x)
                    min_y = min(min_y, point.y)
                    max_x = max(max_x, point.x)
                    max_y = max(max_y, point.y)

    return (min_x, min_y, max_x, max_y)


def boxes_overlap(
    box1: tuple[float, float, float, float],
    box2: tuple[float, float, float, float],
    margin_allowance: int,
    overlap_threshold: int,
) -> bool:  # pragma: no cover
    """Check if two bounding boxes overlap."""
    min_x1, min_y1, max_x1, max_y1 = box1
    min_x2, min_y2, max_x2, max_y2 = box2
    # if one of the boxes is larger than overlap_threshold, we consider it as a full page and return no.
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
        seqno = drawings[i].get("seqno", i)
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
            cp1_x = current_x + 2.0 / 3.0 * (p1.x - current_x)
            cp1_y = current_y + 2.0 / 3.0 * (p1.y - current_y)
            cp2_x = p2.x + 2.0 / 3.0 * (p1.x - p2.x)
            cp2_y = p2.y + 2.0 / 3.0 * (p1.y - p2.y)
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


MAX_DIMENSION = 32000


def render_group_to_image(group_drawings) -> RenderedVectorImage:
    # Compute the overall bounding box for the group
    # Only use drawable elements (not clips/groups) for bounding box calculation
    drawable_items = [d for d in group_drawings if d.get("type") not in ["clip", "group"]]
    if not drawable_items:
        return RenderedVectorImage(image=b"", width=0, height=0)

    bounding_boxes = [compute_bounding_box(d) for d in drawable_items]
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
        return RenderedVectorImage(image=b"", width=0, height=0)

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

    # Draw each element in the group, handling clips and level changes
    current_level = 0

    for drawing in group_drawings:
        drawing_type = drawing.get("type", "")
        drawing_level = drawing.get("level", 0)

        # When level decreases, restore context states
        while current_level > drawing_level:
            ctx.restore()
            current_level -= 1

        # Handle clip elements - they define clipping regions
        if drawing_type == "clip":
            ctx.save()
            current_level += 1

            if "items" in drawing:
                ctx.new_path()
                parse_items_and_draw_cairo(ctx, drawing["items"])
                if drawing.get("even_odd", False):
                    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
                else:
                    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
                ctx.clip()
            continue

        # Handle group elements - they may set blend modes and opacity
        if drawing_type == "group":
            ctx.save()
            current_level += 1

            # Apply blend mode if specified
            blendmode = drawing.get("blendmode")
            if blendmode:
                # Map PDF blend modes to Cairo operators
                blend_map = {
                    "Normal": cairo.OPERATOR_OVER,
                    "Multiply": cairo.OPERATOR_MULTIPLY,
                    "Screen": cairo.OPERATOR_SCREEN,
                    "Overlay": cairo.OPERATOR_OVERLAY,
                    "Darken": cairo.OPERATOR_DARKEN,
                    "Lighten": cairo.OPERATOR_LIGHTEN,
                    "ColorDodge": cairo.OPERATOR_COLOR_DODGE,
                    "ColorBurn": cairo.OPERATOR_COLOR_BURN,
                    "HardLight": cairo.OPERATOR_HARD_LIGHT,
                    "SoftLight": cairo.OPERATOR_SOFT_LIGHT,
                    "Difference": cairo.OPERATOR_DIFFERENCE,
                    "Exclusion": cairo.OPERATOR_EXCLUSION,
                }
                operator = blend_map.get(blendmode, cairo.OPERATOR_OVER)
                ctx.set_operator(operator)

            continue

        # Render drawable elements
        if "items" not in drawing:
            continue

        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        ctx.new_path()
        parse_items_and_draw_cairo(ctx, drawing["items"])

        has_fill = "f" in drawing_type
        has_stroke = "s" in drawing_type

        # Get general opacity (affects both fill and stroke)
        general_opacity = drawing.get("opacity") or 1.0

        if has_fill:
            fill_color = convert_color_cairo(drawing.get("fill")) if drawing.get("fill") else (0, 0, 0)
            fill_opacity = (drawing.get("fill_opacity") or 1.0) * general_opacity
            ctx.set_source_rgba(*fill_color, fill_opacity)
            if has_stroke:
                ctx.fill_preserve()
            else:
                ctx.fill()

        if has_stroke:
            stroke_color = convert_color_cairo(drawing.get("color")) if drawing.get("color") else (0, 0, 0)
            stroke_width = drawing.get("width", 1)
            stroke_opacity = (drawing.get("stroke_opacity") or 1.0) * general_opacity
            ctx.set_source_rgba(*stroke_color, stroke_opacity)
            ctx.set_line_width(stroke_width)
            ctx.stroke()

    # Restore any remaining saved states
    while current_level > 0:
        ctx.restore()
        current_level -= 1

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
    """Renders the passed in PDF drawings to images, using bounding box overlap grouping."""
    # Filter to only drawable elements (not clips/groups which are structural)
    drawable_items = [d for d in drawings if d.get("type") not in ["clip", "group"]]

    # Group by bounding box overlap
    groups = group_overlapping_drawings(drawable_items, margin_allowance, overlap_threshold)

    # For each group, include relevant clip/group elements from the original drawings
    # by finding clips/groups that affect the drawable items in each group
    enriched_groups = []
    for group in groups:
        # Get seqnos of drawables in this group
        group_seqnos = {d.get("seqno", -1) for d in group}

        # Find all elements (including clips/groups) that should be part of this group
        # Include clips/groups that come before the first drawable in this group
        min_seqno = min(group_seqnos) if group_seqnos else float("inf")

        enriched_group = []
        for drawing in drawings:
            seqno = drawing.get("seqno", -1)
            dtype = drawing.get("type", "")

            # Include this drawing if:
            # 1. It's in the drawable group, OR
            # 2. It's a clip/group that comes before the group's drawables
            if seqno in group_seqnos or (dtype in ["clip", "group"] and seqno < min_seqno):
                enriched_group.append(drawing)

        if enriched_group:
            enriched_groups.append(enriched_group)

    results = [render_group_to_image(group) for group in enriched_groups]
    return [r for r in results if r.width > 0 and r.height > 0]  # Filter out empty images
