import enum

from pydantic import BaseModel


class TextGroupType(str, enum.Enum):
    heading = "heading"
    stanza = "stanza"
    list = "list"
    paragraph = "paragraph"
    other = "other"


class TextType(str, enum.Enum):
   
    # Simplified 2
    heading_text = "heading_text"
    paragraph_text = "paragraph_text"
    floating_text = "floating_text"
    math = "math"
    page_header = "page_header"
    page_footer = "page_footer"
    page_number = "page_number"
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
    text_type: str
    language_code: str
    text: str
    reasoning: str
