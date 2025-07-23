import io
import math

import cairo
from pydantic import BaseModel


class RenderedVectorImage(BaseModel):
    image: bytes
    width: int
    height: int


def convert_color_cairo(color: list[float]) -> tuple[float, ...]:
    """Convert a float-based color to a Cairo color with a default."""
    return tuple(c for c in color) if color else (0, 0, 0)


def compute_bounding_box(drawing) -> tuple[float, float, float, float]:  # pragma: no cover
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
        elif cmd in ("m", "l"):
            p = item[1]
            min_x = min(min_x, p.x)
            min_y = min(min_y, p.y)
            max_x = max(max_x, p.x)
            max_y = max(max_y, p.y)
        elif cmd == "c":
            p1, p2, p3 = item[1], item[2], item[3]
            min_x = min(min_x, p1.x, p2.x, p3.x)
            min_y = min(min_y, p1.y, p2.y, p3.y)
            max_x = max(max_x, p1.x, p2.x, p3.x)
            max_y = max(max_y, p1.y, p2.y, p3.y)
        elif cmd == "h":
            # 'h' (close path) does not add any new points
            pass
        elif cmd == "qu":
            quad = item[1]
            p1, p2, p3, p4 = quad[0], quad[1], quad[3], quad[2]
            min_x = min(min_x, p1.x, p2.x, p3.x, p4.x)
            min_y = min(min_y, p1.y, p2.y, p3.y, p4.y)
            max_x = max(max_x, p1.x, p2.x, p3.x, p4.x)
            max_y = max(max_y, p1.y, p2.y, p3.y, p4.y)

    # Handle cases where no drawing commands were found
    if min_x == float("inf") or min_y == float("inf"):
        min_x, min_y, max_x, max_y = 0, 0, 10, 10  # Default small size

    return min_x, min_y, max_x, max_y


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
        groups[root].append(drawings[i])

    return list(groups.values())


def parse_items_and_draw_cairo(ctx, items):  # pragma: no cover
    """Parse the drawing items and draw on the Cairo context."""
    for item in items:
        cmd = item[0]
        if cmd == "m":  # Move to
            p = item[1]
            ctx.move_to(p.x, p.y)
        elif cmd == "l":  # Line to
            p = item[1]
            ctx.line_to(p.x, p.y)
        elif cmd == "c":  # Curve to
            p1, p2, p3 = item[1], item[2], item[3]
            ctx.curve_to(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)
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


def render_group_to_image(group_drawings):  # pragma: no cover
    """Render a group of drawings to a single image file."""
    # Compute the overall bounding box for the group
    bounding_boxes = [compute_bounding_box(d) for d in group_drawings]
    min_x = min(box[0] for box in bounding_boxes)
    min_y = min(box[1] for box in bounding_boxes)
    max_x = max(box[2] for box in bounding_boxes)
    max_y = max(box[3] for box in bounding_boxes)

    width = int(math.ceil(max_x - min_x))
    height = int(math.ceil(max_y - min_y))

    # Ensure minimum dimensions
    if width <= 0:
        width = 10
    if height <= 0:
        height = 10

    # Create a Cairo surface and context for the group
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    # Fill the background with white
    ctx.set_source_rgb(1, 1, 1)  # White
    ctx.rectangle(0, 0, width, height)
    ctx.fill()

    # Translate the context so that the group's top-left corner is at (0, 0)
    ctx.translate(-min_x, -min_y)

    # Draw each drawing in the group
    for drawing in group_drawings:
        ctx.new_path()  # Start a new path for each drawing
        parse_items_and_draw_cairo(ctx, drawing["items"])

        # Handle filling and stroking based on the drawing type
        drawing_type = drawing.get("type", "")

        if "f" in drawing_type:  # Filled Path
            fill_color = convert_color_cairo(drawing.get("fill")) if drawing.get("fill") else (0, 0, 0)
            ctx.set_source_rgb(*fill_color)
            fill_rule = cairo.FILL_RULE_EVEN_ODD if drawing.get("even_odd", False) else cairo.FILL_RULE_WINDING
            ctx.set_fill_rule(fill_rule)
            ctx.fill_preserve()  # Preserve the path for potential stroking

        if "s" in drawing_type:  # Stroked Path
            stroke_color = convert_color_cairo(drawing.get("color")) if drawing.get("color") else (0, 0, 0)
            stroke_width = drawing.get("width", 1)
            ctx.set_source_rgb(*stroke_color)
            ctx.set_line_width(stroke_width)
            ctx.stroke()
        elif "f" in drawing_type:
            # If only filling, optionally stroke the path after filling
            ctx.stroke()

    # Get the final image width and height.
    width, height = surface.get_width(), surface.get_height()

    # write our PNG
    buffer = io.BytesIO()
    surface.write_to_png(buffer)
    buffer.seek(0)
    return RenderedVectorImage(image=buffer.getvalue(), width=width, height=height)


def render_drawings(drawings, margin_allowance: int, overlap_threshold: int) -> list[RenderedVectorImage]:
    """Renders the passed in PDF drawing to images, grouping overlapping drawings."""
    groups = group_overlapping_drawings(drawings, margin_allowance, overlap_threshold)
    results = [render_group_to_image(group) for group in groups]
    return results
