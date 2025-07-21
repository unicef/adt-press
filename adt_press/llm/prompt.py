from typing import Self

from pydantic import BaseModel, Field, model_validator

from adt_press.utils.file import calculate_file_hash


class PromptConfig(BaseModel):
    model: str
    template_path: str
    template_hash: str = Field(default=None, exclude=True)
    examples: list[dict] = []
    rate_limit: int = 300

    @model_validator(mode="after")
    def set_template_hash(self) -> Self:
        self.template_hash = calculate_file_hash(self.template_path)
        return self
