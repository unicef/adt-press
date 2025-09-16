from pydantic import BaseModel

from adt_press.models.image import Image


class Page(BaseModel):
    page_id: str
    page_number: int
    page_image_path: str
    text: str
    images: list[Image]
