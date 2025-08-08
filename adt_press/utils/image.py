import io
import warnings
from dataclasses import dataclass
from typing import List, Tuple

import cv2
import fitz
import matplotlib.pyplot as plt
import numpy as np
import PIL
import PIL.ImageDraw
from fsspec import open
from pydantic import BaseModel

plt.switch_backend("Agg")
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Set the figure.max_open_warning to a high number to suppress the warning
plt.rcParams.update({"figure.max_open_warning": 100})

# We need to set this zoom for PyMuPDF or the image is pixelated.
FITZ_ZOOM = 2
FITZ_MAT = fitz.Matrix(FITZ_ZOOM, FITZ_ZOOM)


class Image(BaseModel):
    image_id: str
    upath: str
    chart_upath: str

    page_id: str
    index: int

    width: float  # Changed to float for points
    height: float  # Changed to float for points
    
    # Add fields for composite images and better spatial awareness
    is_composite: bool = False
    component_count: int = 1
    bbox_points: tuple[float, float, float, float] | None = None

    @property
    def width_points(self) -> float:
        """Get width in points, preferring bbox_points if available."""
        bbox_points = getattr(self, 'bbox_points', None)
        if bbox_points:
            return bbox_points[2] - bbox_points[0]
        return self.width

    @property
    def height_points(self) -> float:
        """Get height in points, preferring bbox_points if available."""
        bbox_points = getattr(self, 'bbox_points', None)
        if bbox_points:
            return bbox_points[3] - bbox_points[1]
        return self.height


class ImageFilterFailure(BaseModel):
    image_id: str
    filter: str
    reasoning: str | None


class ImageCaption(BaseModel):
    image_id: str
    caption: str
    reasoning: str


class ImageMeaningfulness(BaseModel):
    image_id: str
    is_meaningful: bool
    reasoning: str


class CropCoordinates(BaseModel):
    top_left_x: int
    top_left_y: int
    bottom_right_x: int
    bottom_right_y: int


class ImageCrop(BaseModel):
    image_id: str
    crop_coordinates: CropCoordinates
    upath: str


class PrunedImage(Image):
    failed_filters: list[ImageFilterFailure] = []


class ProcessedImage(Image):
    caption: ImageCaption
    crop: ImageCrop
    meaningfulness: ImageMeaningfulness


@dataclass
class VectorElement:
    bbox: fitz.Rect
    content: dict | tuple  # Can be drawing dict or image tuple
    element_type: str  # 'path', 'image', 'text'
    
    # Additional classification attributes
    is_large_background: bool = False
    is_likely_text: bool = False
    complexity: int = 0


def image_bytes(image_path: str) -> bytes:
    """Returns the bytes of an image given its path."""

    with open(image_path, "rb") as f:
        return bytes(f.read())


def is_blank_image(image_bytes: bytes, threshold: int) -> bool:
    """
    Checks if an image is blank (completely single color blank background). By default set to a low pixel standard deviation threshold of 2, if the image's
    pixel standard deviation is below this threshold, the image is considered blank.
    :param image_bytes: The bytes of the image to check.
    :param threshold: The threshold value to consider small variations due to compression or noise.
    :return: True if the image is blank, False otherwise.
    """

    # Convert the image data to a numpy array
    image_array = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)
    assert image is not None, "Image could not be decoded from bytes."
    # Compute the standard deviation of the pixel values
    std_dev = np.std(image)
    # Check if the standard deviation is below the threshold
    return bool(std_dev < threshold)


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


def crop_image(img_bytes: bytes, crop: CropCoordinates) -> bytes:
    """Crops the image bytes according to the provided coordinates and returns the cropped image as bytes."""

    image = PIL.Image.open(io.BytesIO(img_bytes))
    cropped_image = image.crop((crop.top_left_x, crop.top_left_y, crop.bottom_right_x, crop.bottom_right_y))
    buffer = io.BytesIO()
    cropped_image.save(buffer, format="png")
    buffer.seek(0)
    return buffer.getvalue()


def visualize_crop_extents(image_bytes: bytes, top_left_x, top_left_y, bottom_right_x, bottom_right_y) -> bytes:
    """
    Draws a transparent rectangle on the image to visualize the crop coordinates.
    """
    im = PIL.Image.open(io.BytesIO(image_bytes))
    draw = PIL.ImageDraw.Draw(im)

    # Draw a semi-transparent rectangle
    draw.rectangle([top_left_x, top_left_y, bottom_right_x, bottom_right_y], outline="red", width=2)

    buf = io.BytesIO()
    im.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def extract_vector_groups(page: fitz.Page, proximity_threshold: float = 30.0) -> List[List[VectorElement]]:
    """
    Extract vector elements and group them by spatial proximity.
    
    Args:
        page: PyMuPDF page object
        proximity_threshold: Distance in points to consider elements as related
    """
    elements = []
    
    try:
        # Get all drawing commands/paths
        for item in page.get_drawings():
            # Calculate bounding box for this drawing
            bbox = _compute_drawing_bbox(item)
            # Add classification info to help with grouping decisions
            element = VectorElement(
                bbox=bbox,
                content=item,
                element_type='path',
                is_large_background=_is_large_background_element(bbox, page),
                is_likely_text=_is_likely_text_element(item, bbox),
                complexity=_estimate_drawing_complexity(item)
            )
            elements.append(element)
        
        # Get images that might be part of the illustration
        for img_index, img in enumerate(page.get_images()):
            try:
                img_rect = page.get_image_bbox(img[0])
                element = VectorElement(
                    bbox=img_rect,
                    content=img,
                    element_type='image',
                    is_large_background=_is_large_background_element(img_rect, page),
                    is_likely_text=False,
                    complexity=1  # Images have low complexity score
                )
                elements.append(element)
            except (ValueError, RuntimeError):
                # Skip images we can't get bbox for
                continue
        
        # Group elements by proximity with intelligent filtering
        return group_by_proximity_smart(elements, proximity_threshold)
    except Exception as e:
        # Fallback to individual elements if grouping fails
        warnings.warn(f"Vector grouping failed: {e}, falling back to individual elements")
        return [[element] for element in elements]


def _compute_drawing_bbox(drawing) -> fitz.Rect:
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

    return fitz.Rect(min_x, min_y, max_x, max_y)


def group_by_proximity(elements: List[VectorElement], threshold: float) -> List[List[VectorElement]]:
    """Group elements that are close to each other spatially."""
    if not elements:
        return []
    
    groups = []
    remaining = elements.copy()
    
    while remaining:
        current_group = [remaining.pop(0)]
        group_bbox = current_group[0].bbox
        
        # Keep adding nearby elements to the current group
        changed = True
        while changed:
            changed = False
            to_remove = []
            
            for i, element in enumerate(remaining):
                # Check if element is close to any element in current group
                if is_near_group(element.bbox, group_bbox, threshold):
                    current_group.append(element)
                    group_bbox = group_bbox | element.bbox  # Expand bounding box
                    to_remove.append(i)
                    changed = True
            
            # Remove elements that were added to the group
            for i in reversed(to_remove):
                remaining.pop(i)
        
        groups.append(current_group)
    
    return groups


def is_near_group(element_bbox: fitz.Rect, group_bbox: fitz.Rect, threshold: float) -> bool:
    """Check if an element is close enough to a group to be included."""
    # Calculate minimum distance between rectangles
    dx = max(0, max(group_bbox.x0 - element_bbox.x1, element_bbox.x0 - group_bbox.x1))
    dy = max(0, max(group_bbox.y0 - element_bbox.y1, element_bbox.y0 - group_bbox.y1))
    distance = (dx**2 + dy**2)**0.5
    
    return distance <= threshold


def create_composite_image(page: fitz.Page, element_group: List[VectorElement], dpi: int = 300) -> bytes:
    """
    Create a single raster image from a group of vector elements.
    
    Args:
        page: PyMuPDF page object
        element_group: List of related vector elements
        dpi: Resolution for rasterization
    """
    try:
        # Calculate overall bounding box for the group
        overall_bbox = element_group[0].bbox
        for element in element_group[1:]:
            overall_bbox = overall_bbox | element.bbox
        
        # Add small padding
        padding = 10  # points
        overall_bbox = fitz.Rect(
            overall_bbox.x0 - padding,
            overall_bbox.y0 - padding, 
            overall_bbox.x1 + padding,
            overall_bbox.y1 + padding
        )
        
        # Create a clip rectangle and render at high resolution
        zoom = dpi / 72.0  # Convert DPI to zoom factor
        mat = fitz.Matrix(zoom, zoom)
        
        # Render the clipped area
        pix = page.get_pixmap(matrix=mat, clip=overall_bbox)
        img_data = pix.tobytes("png")
        pix = None  # Free memory
        
        return img_data
    except Exception as e:
        warnings.warn(f"Composite image creation failed: {e}, creating minimal placeholder")
        # Create a minimal 100x100 white image as fallback
        import PIL.Image
        img = PIL.Image.new('RGB', (100, 100), 'white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()


def get_group_bbox(group: List[VectorElement]) -> fitz.Rect:
    """Get overall bounding box for a group of elements."""
    bbox = group[0].bbox
    for element in group[1:]:
        bbox = bbox | element.bbox
    return bbox


def get_group_size_points(group: List[VectorElement]) -> Tuple[float, float]:
    """Get width and height of group in points."""
    bbox = get_group_bbox(group)
    return (bbox.width, bbox.height)


def _is_large_background_element(bbox: fitz.Rect, page: fitz.Page) -> bool:
    """Check if this element is likely a large background element."""
    page_rect = page.rect
    element_area = bbox.width * bbox.height
    page_area = page_rect.width * page_rect.height
    
    # If element covers more than 50% of page area, it's likely background
    area_ratio = element_area / page_area
    return area_ratio > 0.5 or bbox.width > page_rect.width * 0.8 or bbox.height > page_rect.height * 0.8


def _is_likely_text_element(drawing: dict, bbox: fitz.Rect) -> bool:
    """Check if this drawing is likely text-related."""
    # Text elements are usually small and have simple geometry
    items = drawing.get("items", [])
    
    # Very small elements (< 5 points) are likely text fragments
    if bbox.width < 5 or bbox.height < 5:
        return True
    
    # Elements with very high aspect ratios might be text lines
    aspect_ratio = max(bbox.width, bbox.height) / min(bbox.width, bbox.height)
    if aspect_ratio > 10:
        return True
    
    # Simple rectangular elements in typical text regions might be text
    if len(items) == 1 and items[0][0] == "re":  # Single rectangle
        return True
    
    return False


def _estimate_drawing_complexity(drawing: dict) -> int:
    """Estimate the complexity of a drawing (higher = more complex)."""
    items = drawing.get("items", [])
    complexity = 0
    
    for item in items:
        cmd = item[0]
        if cmd in ("m", "l"):  # Move/line commands
            complexity += 1
        elif cmd == "c":  # Curve commands
            complexity += 2
        elif cmd == "re":  # Rectangle commands
            complexity += 1
        elif cmd == "qu":  # Quad commands
            complexity += 2
    
    return complexity


def group_by_proximity_smart(elements: List[VectorElement], threshold: float) -> List[List[VectorElement]]:
    """Group elements that are close to each other spatially, with intelligent filtering."""
    if not elements:
        return []
    
    # Filter out elements that shouldn't be grouped
    illustration_elements = [
        el for el in elements 
        if not el.is_large_background 
        and not el.is_likely_text
        and el.complexity > 2  # Only group more complex elements
    ]
    
    # Group the filtered elements
    groups = []
    remaining = illustration_elements.copy()
    
    while remaining:
        current_group = [remaining.pop(0)]
        group_bbox = current_group[0].bbox
        
        # Keep adding nearby elements to the current group
        changed = True
        while changed:
            changed = False
            to_remove = []
            
            for i, element in enumerate(remaining):
                # Check if element is close to any element in current group
                if is_near_group_smart(element, current_group, group_bbox, threshold):
                    current_group.append(element)
                    group_bbox = group_bbox | element.bbox  # Expand bounding box
                    to_remove.append(i)
                    changed = True
            
            # Remove elements that were added to the group
            for i in reversed(to_remove):
                remaining.pop(i)
        
        # Only keep groups with multiple elements or sufficiently complex single elements
        if len(current_group) > 1 or current_group[0].complexity > 5:
            groups.append(current_group)
    
    # Add back individual elements that weren't grouped as separate groups
    individual_elements = [
        el for el in elements 
        if not any(el in group for group in groups)
        and not el.is_large_background
        and not el.is_likely_text
    ]
    
    for element in individual_elements:
        groups.append([element])
    
    return groups


def is_near_group_smart(element: VectorElement, group: List[VectorElement], group_bbox: fitz.Rect, threshold: float) -> bool:
    """Check if an element should be grouped with others, considering element characteristics."""
    # Basic proximity check
    dx = max(0, max(group_bbox.x0 - element.bbox.x1, element.bbox.x0 - group_bbox.x1))
    dy = max(0, max(group_bbox.y0 - element.bbox.y1, element.bbox.y0 - group_bbox.y1))
    distance = (dx**2 + dy**2)**0.5
    
    if distance > threshold:
        return False
    
    # Don't group very different complexity levels
    element_complexity = element.complexity
    group_complexities = [el.complexity for el in group]
    avg_group_complexity = sum(group_complexities) / len(group_complexities)
    
    # If complexity difference is too large, don't group
    if abs(element_complexity - avg_group_complexity) > 10:
        return False
    
    return True
