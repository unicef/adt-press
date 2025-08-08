from pydantic import BaseModel

from adt_press.models.section import GlossaryItem, SectionType


class PlateText(BaseModel):
    text_id: str
    text: str


class PlateImage(BaseModel):
    image_id: str
    upath: str
    caption: str


class PlateSection(BaseModel):
    section_id: str
    section_type: SectionType
    page_image_upath: str
    part_ids: list[str]
    explanation: str
    easy_read: str
    glossary: list[GlossaryItem]


class Plate(BaseModel):
    title: str
    language_code: str
    sections: list[PlateSection]
    images: list[PlateImage]
    texts: list[PlateText]
