from typing import Optional

from pydantic import BaseModel


class Metadata(BaseModel):
    """Metadata extracted from the first pages of a book."""

    title: Optional[str] = None
    authors: list[str] = []
    publisher: Optional[str] = None
    cover_page_id: Optional[str] = None
    reasoning: str
