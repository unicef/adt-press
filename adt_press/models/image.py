from pydantic import BaseModel


class Image(BaseModel):
    image_id: str
    upath: str
    chart_upath: str

    page_id: str
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
