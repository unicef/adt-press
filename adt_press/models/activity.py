import enum
from typing import Any

from pydantic import BaseModel


class ActivityType(str, enum.Enum):
    matching = "matching"
    fill_in_a_table = "fill_in_a_table"
    multiple_choice = "multiple_choice"
    true_false = "true_false"
    open_ended_answer = "open_ended_answer"
    fill_in_the_blank = "fill_in_the_blank"
    sorting = "sorting"


class Activity(BaseModel):
    activity_id: str
    section_id: str
    activity_type: ActivityType
    items: list[dict[str, Any]]
    reasoning: str
