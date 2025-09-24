import enum

from pydantic import BaseModel

class TextGroupType(str, enum.Enum):
    stanza = "stanza"
    list = "list"
    paragraph = "paragraph"
    other = "other"
    

class TextType(str, enum.Enum):
    book_title = "book_title"
    book_subtitle = "book_subtitle"
    book_author = "book_author"
    chapter_title = "chapter_title"
    section_heading = "section_heading"
    section_text = "section_text"
    boxed_text = "boxed_text"
    hint = "hint"
    instruction_text = "instruction_text"
    activity_number = "activity_number"
    activity_option = "activity_option"
    activity_input_placeholder_text = "activity_input_placeholder_text"
    image_label = "image_label"
    image_caption = "image_caption"
    image_overlay = "image_overlay"
    math = "math"
    standalone_text = "standalone_text"
    page_number = "page_number"
    footer_text = "footer_text"
    other = "other"


class EasyReadText(BaseModel):
    easy_read_id: str
    text_id: str
    easy_read: str
    reasoning: str


class PageText(BaseModel):
    text_id: str
    text: str
    text_type: TextType
    is_pruned: bool = False

class PageTextGroup(BaseModel):
    group_id: str
    group_type: TextGroupType
    texts: list[PageText]

class PageTexts(BaseModel):
    page_id: str
    groups: list[PageTextGroup]
    reasoning: str

class OutputText(BaseModel):
    text_id: str
    language_code: str
    text: str
    reasoning: str
