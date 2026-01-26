from pydantic import BaseModel

from adt_press.models.config import SectionTypeName
from adt_press.models.ids import ChapterID, ImageID, QuizExplanationID, QuizID, QuizOptionID, QuizQuestionID, SectionID, TextGroupID, TextID
from adt_press.models.section import GlossaryItem
from adt_press.utils.languages import LanguageCode


class PlateText(BaseModel):
    text_id: TextID
    text_type: str
    text: str


class PlateGroup(BaseModel):
    group_id: TextGroupID
    group_type: str
    text_ids: list[TextID]


class PlateImage(BaseModel):
    image_id: ImageID
    image_path: str
    caption_id: TextID


class PlateSection(BaseModel):
    section_id: SectionID
    section_type: SectionTypeName
    page_number: int | None
    page_image_path: str
    part_ids: list[str]
    explanation_id: str | None
    background_color: str
    text_color: str
    # Layout hint for HTML generation - describes how content should be arranged
    # Options: "stacked" (default), "text_left_image_right", "image_left_text_right",
    #          "image_top", "two_column_text", "grid_images"
    layout_hint: str = "stacked"


class PlateQuiz(BaseModel):
    quiz_id: QuizID
    section_id: SectionID
    question_id: QuizQuestionID
    option_ids: list[QuizOptionID]
    explanation_ids: list[QuizExplanationID]
    answer_index: int


class PlateChapter(BaseModel):
    chapter_id: ChapterID
    section_id: SectionID


class Plate(BaseModel):
    title: str
    language_code: LanguageCode
    authors: list[str]
    table_of_contents: list[PlateChapter]
    publisher: str | None
    cover_image_id: ImageID | None
    sections: list[PlateSection]
    images: list[PlateImage]
    groups: list[PlateGroup]
    quizzes: list[PlateQuiz]
    texts: list[PlateText]
    glossary: list[GlossaryItem]
