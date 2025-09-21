from pydantic import BaseModel

from adt_press.models.section import GlossaryItem, SectionType


class PlateText(BaseModel):
    text_id: str
    text: str


class PlateImage(BaseModel):
    image_id: str
    image_path: str
    caption_id: str


class PlateSection(BaseModel):
    section_id: str
    section_type: SectionType
    page_image_path: str
    part_ids: list[str]
    explanation_id: str | None
    background_color: str
    text_color: str
    layout_type: str


class Plate(BaseModel):
    title: str
    language_code: str
    sections: list[PlateSection]
    images: list[PlateImage]
    texts: list[PlateText]
    glossary: list[GlossaryItem]
