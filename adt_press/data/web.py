from pydantic import BaseModel


class WebPage(BaseModel):
    text_id: str
    section_id: str
    reasoning: str
    content: str
    text_ids: list[str]
    image_ids: list[str]
