import io
import warnings

import cv2
import fitz
import matplotlib.pyplot as plt
import numpy as np
import PIL
import PIL.ImageDraw
from fsspec import open
from pydantic import BaseModel

from adt_press.data.image import CropCoordinates

plt.switch_backend("Agg")
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Set the figure.max_open_warning to a high number to suppress the warning
plt.rcParams.update({"figure.max_open_warning": 100})

# We need to set this zoom for PyMuPDF or the image is pixelated.
FITZ_ZOOM = 2
FITZ_MAT = fitz.Matrix(FITZ_ZOOM, FITZ_ZOOM)


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
