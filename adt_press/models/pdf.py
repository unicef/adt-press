from pydantic import BaseModel

from adt_press.models.image import Image


class Page(BaseModel):
    page_id: str
    page_number: int
    image_upath: str
    text: str
    images: list[Image]
