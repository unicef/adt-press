
import enum

from pydantic import BaseModel


class ExtractedTextType(str, enum.Enum):
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

class PageText(BaseModel):
    text_id: str
    text: str
    type: ExtractedTextType
    is_pruned: bool = False


class PageTexts(BaseModel):
    page_id: str
    texts: list[PageText]
    reasoning: str

class OutputText(BaseModel):
    text_id: str
    language_code: str
    text: str
    reasoning: str