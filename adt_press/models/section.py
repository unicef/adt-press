from pydantic import BaseModel

from adt_press.models.config import SectionType


class PageSection(BaseModel):
    section_id: str
    section_type: SectionType
    part_ids: list[str] = []
    is_pruned: bool = False


class SectionExplanation(BaseModel):
    explanation_id: str
    section_id: str
    reasoning: str
    explanation: str


class GlossaryItem(BaseModel):
    word: str
    variations: list[str]
    definition: str
    emojis: list[str]


class SectionGlossary(BaseModel):
    section_id: str
    items: list[GlossaryItem]
    reasoning: str


class SectionMetadata(BaseModel):
    section_id: str
    background_color: str
    text_color: str
    layout_type: str
    reasoning: str


class ActivityAnswer(BaseModel):
    section_id: str
    answers: dict[str, str]
    reasoning: str


class PageSections(BaseModel):
    page_id: str
    sections: list[PageSection]
    reasoning: str
