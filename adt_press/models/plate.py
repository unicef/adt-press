from pydantic import BaseModel

from adt_press.models.section import GlossaryItem, SectionType


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
    section_type: SectionType
    page_image_path: str
    part_ids: list[str]
    explanation_id: str | None
    background_color: str
    text_color: str
    layout_type: str

    
class PlateQuiz(BaseModel):
    quiz_id: str
    section_id: str
    question_id: str
    option_ids: list[str]
    explanation_ids: list[str]
    answer_index: int


class Plate(BaseModel):
    title: str
    language_code: str
    sections: list[PlateSection]
    images: list[PlateImage]
    groups: list[PlateGroup]
    quizzes: list[PlateQuiz]
    texts: list[PlateText]
    glossary: list[GlossaryItem]
