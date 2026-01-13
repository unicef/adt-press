from pydantic import BaseModel

from adt_press.models.config import TextGroupTypeName, TextTypeName
from adt_press.models.ids import EasyReadID, OutputTextID, PageID, TextGroupID, TextID


class EasyReadText(BaseModel):
    easy_read_id: EasyReadID
    text_id: TextID
    easy_read: str
    reasoning: str


class Text(BaseModel):
    text_id: TextID
    text: str
    text_type: TextTypeName
    is_pruned: bool = False


class TextGroup(BaseModel):
    group_id: TextGroupID
    group_type: TextGroupTypeName
    texts: list[Text]


class PageTextGroups(BaseModel):
    page_id: PageID
    groups: list[TextGroup]
    reasoning: str


class OutputText(BaseModel):
    text_id: OutputTextID
    text_type: TextTypeName
    language_code: str
    text: str
    reasoning: str
