from pydantic import BaseModel, Field

from adt_press.models.plate import PlateText


class RenderTextGroup(BaseModel):
    group_id: str
    group_type: str
    texts: list[PlateText]


class WebPage(BaseModel):
    section_id: str
    text_id: str | None = None
    text_ids: list[str] = Field(default_factory=list)
    image_ids: list[str] = Field(default_factory=list)
    generated_texts: list[PlateText] = Field(default_factory=list)
    content: str
    reasoning: str = ""
    render_strategy: str = ""
    activity_answers: dict[str, str | bool | int | float] = Field(default_factory=dict)
    activity_reasoning: str = ""
    formatted_texts: dict[str, str] = Field(
        default_factory=dict,
        description="Formatted HTML text content for each text_id (for translations.json)",
    )
