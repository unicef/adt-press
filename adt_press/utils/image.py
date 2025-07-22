import io
import warnings
from functools import cache

import cv2
import fitz
import matplotlib.pyplot as plt
import numpy as np
import PIL
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

    page: int
    index: int

    width: int
    height: int


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


@cache
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
    if image is None:
        raise ValueError("Image not found or unable to read the file.")
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


def write_image(output_path: str, image_bytes: bytes, suffix: str = "") -> str:
    """Writes the image bytes to the specified output path, optionally appending a suffix to the filename."""

    # if we have a suffix, add it in after removing the extension
    if suffix != "":
        output_path = output_path.rsplit(".", 1)[0] + f"_{suffix}." + output_path.rsplit(".", 1)[1]

    with open(output_path, "wb") as f:
        f.write(image_bytes)

    return output_path
