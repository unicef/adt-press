from pydantic import BaseModel, Field

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
    activity_answers: dict[str, str] | None = None
    generated_texts: list[PlateText] = Field(default_factory=list)
