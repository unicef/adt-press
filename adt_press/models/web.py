from pydantic import BaseModel

from adt_press.models.plate import PlateText

class RenderTextGroup(BaseModel):
    group_id: str
    group_type: str
    texts: list[PlateText]

class WebPage(BaseModel):
    text_id: str
    section_id: str
    reasoning: str
    content: str
    text_ids: list[str]
    image_ids: list[str]
    render_strategy: str
