from pydantic import BaseModel

from adt_press.models.ids import ChapterID


class BookChapter(BaseModel):
    chapter_id: ChapterID
    title: str
    page_number: int


class BookMetadata(BaseModel):
    """Metadata extracted from the first pages of the book"""

    title: str | None = None
    authors: list[str] = []
    publisher: str | None = None
    language_code: str | None = None
    cover_page_id: str | None = None
    table_of_contents: list[BookChapter] = []
    reasoning: str
