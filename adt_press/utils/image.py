import io
import os
import warnings
from collections.abc import Sequence

import cv2
import matplotlib.pyplot as plt
import numpy as np
import PIL
import PIL.ImageDraw
from fsspec import open

from adt_press.models.image import CropCoordinates

plt.switch_backend("Agg")
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Set the figure.max_open_warning to a high number to suppress the warning
plt.rcParams.update({"figure.max_open_warning": 100})


def _coerce_extrema_value(value: object) -> int:
    """Return a scalar int from extrema outputs that may nest tuples/lists."""

    current = value
    while (
        isinstance(current, Sequence)
        and not isinstance(current, (str, bytes, bytearray))
    ):
        if not current:
            raise ValueError("Extrema sequence is empty.")
        current = current[0]

    if isinstance(current, (int, float)):
        return int(current)

    raise TypeError(f"Unsupported extrema value type: {type(current)!r}")


def _has_visible_alpha(image: PIL.Image.Image) -> bool:
    """Return True if any pixel is partially transparent."""

    if image.mode in ("RGBA", "LA"):
        alpha = image.getchannel("A")
        min_alpha_raw, max_alpha_raw = alpha.getextrema()
        min_alpha = _coerce_extrema_value(min_alpha_raw)
        max_alpha = _coerce_extrema_value(max_alpha_raw)
        return min_alpha < 255 or max_alpha < 255

    transparency = image.info.get("transparency")
    if transparency is None:
        return False

    if isinstance(transparency, int):
        return True

    if isinstance(transparency, (bytes, bytearray)):
        return any(value < 255 for value in transparency)

    if isinstance(transparency, (list, tuple)):
        return any(int(value) < 255 for value in transparency)

    return bool(transparency)


def compress_image_for_web(
    src_path: str,
    dest_dir: str,
    base_name: str,
    jpeg_quality: int = 85,
) -> str:
    """Compress an image for web output, returning the generated filename."""

    os.makedirs(dest_dir, exist_ok=True)

    with PIL.Image.open(src_path) as image:
        has_alpha = _has_visible_alpha(image)

        if has_alpha:
            if image.mode not in ("RGBA", "LA"):
                image = image.convert("RGBA")
            filename = f"{base_name}.png"
            save_kwargs: dict[str, object] = {"optimize": True}
        else:
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            filename = f"{base_name}.jpg"
            save_kwargs = {
                "optimize": True,
                "quality": jpeg_quality,
                "progressive": True,
            }

        dest_path = os.path.join(dest_dir, filename)
        image.save(dest_path, **save_kwargs)

    return filename


def image_bytes(image_path: str) -> bytes:
    """Returns the bytes of an image given its path."""

    with open(image_path, "rb") as f:
        return bytes(f.read())


def is_blank_image(image_bytes: bytes, threshold: int) -> bool:
    """Return True when grayscale stddev stays under the limit."""

    # Convert the image data to a numpy array
    image_array = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)
    assert image is not None, "Image could not be decoded from bytes."
    # Compute the standard deviation of the pixel values
    std_dev = np.std(image)
    # Check if the standard deviation is below the threshold
    return bool(std_dev < threshold)


def matplotlib_chart(img_bytes: bytes) -> bytes:
    """Generate a matplotlib chart from bytes and return PNG bytes."""

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
    """Crop the provided bytes per coordinates and return PNG bytes."""

    image = PIL.Image.open(io.BytesIO(img_bytes))
    cropped_image = image.crop(
        (
            crop.top_left_x,
            crop.top_left_y,
            crop.bottom_right_x,
            crop.bottom_right_y,
        )
    )
    buffer = io.BytesIO()
    cropped_image.save(buffer, format="png")
    buffer.seek(0)
    return buffer.getvalue()


def visualize_crop_extents(
    image_bytes: bytes, top_left_x, top_left_y, bottom_right_x, bottom_right_y
) -> bytes:
    """Draw a transparent rectangle to visualize crop coordinates."""
    im = PIL.Image.open(io.BytesIO(image_bytes))
    draw = PIL.ImageDraw.Draw(im)

    # Draw a semi-transparent rectangle
    draw.rectangle(
        [top_left_x, top_left_y, bottom_right_x, bottom_right_y],
        outline="red",
        width=2,
    )

    buf = io.BytesIO()
    im.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()
