from pydantic import BaseModel

from adt_press.models.section import GlossaryItem


class PlateText(BaseModel):
    text_id: str
    text_type: str
    text: str


class PlateGroup(BaseModel):
    group_id: str
    group_type: str
    text_ids: list[str]


class PlateImage(BaseModel):
    image_id: str
    image_path: str
    caption_id: str


class PlateSection(BaseModel):
    section_id: str
    section_type: str
    page_number: int | None
    page_image_path: str
    part_ids: list[str]
    explanation_id: str | None
    background_color: str
    text_color: str


class PlateChapter(BaseModel):
    chapter_id: str
    section_id: str


class Plate(BaseModel):
    title: str
    language_code: str
    authors: list[str]
    table_of_contents: list[PlateChapter]
    publisher: str | None
    cover_image_id: str | None
    sections: list[PlateSection]
    images: list[PlateImage]
    groups: list[PlateGroup]
    texts: list[PlateText]
    glossary: list[GlossaryItem]
