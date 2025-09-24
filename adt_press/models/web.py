from pydantic import BaseModel

class RenderTextGroup(BaseModel):
    group_id: str
    group_type: str
    texts: list[str]

class WebPage(BaseModel):
    text_id: str
    section_id: str
    reasoning: str
    content: str
    text_ids: list[str]
    image_ids: list[str]
    render_strategy: str
