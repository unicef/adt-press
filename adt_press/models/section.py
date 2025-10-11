import enum

from pydantic import BaseModel, model_validator


class SectionType(str, enum.Enum):
    front_cover = "front_cover"
    inside_cover = "inside_cover"
    back_cover = "back_cover"
    separator = "separator"
    credits = "credits"
    foreword = "foreword"
    table_of_contents = "table_of_contents"
    boxed_text = "boxed_text"
    text_only = "text_only"
    text_and_images = "text_and_images"
    images_only = "images_only"
    activity_matching = "activity_matching"
    activity_fill_in_a_table = "activity_fill_in_a_table"
    activity_multiple_choice = "activity_multiple_choice"
    activity_true_false = "activity_true_false"
    activity_open_ended_answer = "activity_open_ended_answer"
    activity_fill_in_the_blank = "activity_fill_in_the_blank"
    activity_labeling = "activity_labeling"
    activity_multiselect = "activity_multiselect"
    activity_sorting = "activity_sorting"
    activity_other = "activity_other"
    other = "other"


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

    @model_validator(mode="after")
    def populate_ids(self):
        """Automatically populate question_id, option_ids, and explanation_ids based on quiz_id."""
        if not self.question_id:
            self.question_id = f"{self.quiz_id}_que"

        if not self.option_ids:
            self.option_ids = [f"{self.quiz_id}_opt_{idx}" for idx in range(len(self.options))]

        if not self.explanation_ids:
            self.explanation_ids = [f"{self.quiz_id}_exp_{idx}" for idx in range(len(self.explanations))]

        return self
