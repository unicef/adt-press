from pydantic import BaseModel


class BookChapter(BaseModel):
    chapter_id: str
    title: str
    page_number: int


class BookMetadata(BaseModel):
    """Metadata extracted from the first pages of the book"""

    title: str | None = None
    authors: list[str] = []
    publisher: str | None = None
    language: str | None = None
    cover_page_id: str | None = None
    table_of_contents: list[BookChapter] = []
    reasoning: str
