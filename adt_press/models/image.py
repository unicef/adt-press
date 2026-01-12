from pydantic import BaseModel
from adt_press.models.ids import PageID, ImageID



class Image(BaseModel):
    image_id: ImageID
    image_path: str
    chart_path: str

    page_id: PageID
    index: int

    width: int
    height: int
    image_type: str


class ImageFilterFailure(BaseModel):
    image_id: ImageID
    filter: str
    reasoning: str | None


class ImageCaption(BaseModel):
    image_id: ImageID
    caption: str
    reasoning: str


class ImageMeaningfulness(BaseModel):
    image_id: ImageID
    is_meaningful: bool
    reasoning: str


class CropCoordinates(BaseModel):
    top_left_x: int
    top_left_y: int
    bottom_right_x: int
    bottom_right_y: int


class ImageCrop(BaseModel):
    image_id: ImageID
    crop_coordinates: CropCoordinates
    image_path: str


class PrunedImage(Image):
    failed_filters: list[ImageFilterFailure] = []


class ProcessedImage(Image):
    caption: ImageCaption | None
    crop: ImageCrop
    meaningfulness: ImageMeaningfulness
