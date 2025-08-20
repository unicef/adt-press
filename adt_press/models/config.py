from typing import Self

from pydantic import BaseModel, Field, model_validator

from adt_press.utils.file import calculate_file_hash


class PromptConfig(BaseModel):
    model: str
    template_path: str
    template_hash: str | None = Field(default=None, exclude=True)
    examples: list[dict] = []
    rate_limit: int = 300
    max_retries: int = 5

    @model_validator(mode="after")
    def set_template_hash(self) -> Self:
        self.template_hash = calculate_file_hash(self.template_path)
        return self


class CropPromptConfig(PromptConfig):
    recrop_template_path: str | None = None
    recrop_template_hash: str | None = Field(default=None, exclude=True)
    recrops: int = 0

    @model_validator(mode="after")
    def set_recrop_template_hash(self) -> Self:
        if self.recrop_template_path:
            self.recrop_template_hash = calculate_file_hash(self.recrop_template_path)
        return self


class RowPromptConfig(PromptConfig):
    row_template_path: str
    row_template_hash: str | None = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def set_row_template_hash(self) -> Self:
        if self.row_template_path:
            self.row_template_hash = calculate_file_hash(self.row_template_path)
        return self


class HTMLPromptConfig(PromptConfig):
    example_dirs: list[str]


class PageRangeConfig(BaseModel):
    start: int = 0
    end: int = 0


class TemplateConfig(BaseModel):
    output_dir: str
