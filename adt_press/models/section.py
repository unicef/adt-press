import enum

from pydantic import BaseModel


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


class PageSections(BaseModel):
    page_id: str
    sections: list[PageSection]
    reasoning: str
