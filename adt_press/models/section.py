from pydantic import BaseModel

from adt_press.models.config import SectionType
from adt_press.models.ids import ExplanationID, PageID, SectionID


class PageSection(BaseModel):
    section_id: SectionID
    section_type: SectionType
    page_number: int | None
    part_ids: list[str] = []
    is_pruned: bool = False
    background_color: str
    text_color: str


class SectionExplanation(BaseModel):
    explanation_id: ExplanationID
    section_id: SectionID
    reasoning: str
    explanation: str


class GlossaryItem(BaseModel):
    word: str
    variations: list[str]
    definition: str
    emojis: list[str]


class SectionGlossary(BaseModel):
    section_id: SectionID
    items: list[GlossaryItem]
    reasoning: str


class ActivityAnswer(BaseModel):
    section_id: SectionID
    answers: dict[str, str | bool | int | float]
    reasoning: str


class PageSections(BaseModel):
    page_id: PageID
    sections: list[PageSection]
    reasoning: str
