from pydantic import BaseModel

from adt_press.models.config import TextGroupTypeName, TextTypeName
from adt_press.models.ids import PageID, TextGroupID, TextID


class EasyReadText(BaseModel):
    easy_read_id: TextID
    text_id: TextID
    easy_read: str
    reasoning: str


class PageText(BaseModel):
    text_id: TextID
    text: str
    text_type: TextTypeName
    is_pruned: bool = False


class PageTextGroup(BaseModel):
    group_id: TextGroupID
    group_type: TextGroupTypeName
    texts: list[PageText]


class PageTexts(BaseModel):
    page_id: PageID
    groups: list[PageTextGroup]
    reasoning: str


class OutputText(BaseModel):
    text_id: TextID
    text_type: TextTypeName
    language_code: str
    text: str
    reasoning: str
