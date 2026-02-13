from pydantic import BaseModel

from adt_press.models.ids import PageID
from adt_press.models.image import Image


class Page(BaseModel):
    page_id: PageID
    book_id: str
    page_number: int
    page_image_path: str
    text: str
    images: list[Image]
