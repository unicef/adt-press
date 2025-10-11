import enum

from pydantic import BaseModel, model_validator

from adt_press.models.config import SectionType


class PageSection(BaseModel):
    section_id: str
    section_type: SectionType
    page_number: int | None
    part_ids: list[str] = []
    is_pruned: bool = False
    background_color: str
    text_color: str


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


class ActivityAnswer(BaseModel):
    section_id: str
    answers: dict[str, str | bool | int | float]
    reasoning: str


class PageSections(BaseModel):
    page_id: str
    sections: list[PageSection]
    reasoning: str

class SectionQuiz(BaseModel):
    quiz_id: str
    section_id: str
    question: str
    question_id: str = ""
    options: list[str]
    option_ids: list[str] = []
    explanations: list[str]
    explanation_ids: list[str] = []
    answer_index: int
    reasoning: str

    @model_validator(mode='after')
    def populate_ids(self):
        """Automatically populate question_id, option_ids, and explanation_ids based on quiz_id."""
        if not self.question_id:
            self.question_id = f"{self.quiz_id}_que"
        
        if not self.option_ids:
            self.option_ids = [f"{self.quiz_id}_opt_{idx}" for idx in range(len(self.options))]
        
        if not self.explanation_ids:
            self.explanation_ids = [f"{self.quiz_id}_exp_{idx}" for idx in range(len(self.explanations))]
        
        return self