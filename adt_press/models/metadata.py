from pydantic import BaseModel


class BookMetadata(BaseModel):
    """Metadata extracted from the first pages of the book"""

    title: str | None = None
    authors: list[str] = []
    publisher: str | None = None
    cover_page_id: str | None = None
    reasoning: str
