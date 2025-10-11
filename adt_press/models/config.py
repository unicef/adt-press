import enum
import os
from typing import Self

import yaml
from pydantic import BaseModel, Field, model_validator

from adt_press.utils.file import calculate_file_hash, read_text_file


class RenderType(str, enum.Enum):
    html = "html"
    rows = "rows"
    two_column = "two_column"
    template = "template"


class LayoutType(BaseModel):
    name: str
    description: str = ""
    render_strategy: str


class RenderStrategy(BaseModel):
    name: str
    render_type: RenderType
    config: dict
    config_path_hash: str | None = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def set_config_path_hash(self) -> Self:
        """Calculate combined hash of all fields ending in '_path'."""
        path_hashes = []

        # Get all field names that end with '_path'
        for field_name in sorted(self.config.keys()):
            field_value = self.config[field_name]
            if field_name.endswith("_path") and field_value is not None:
                try:
                    file_hash = calculate_file_hash(field_value)
                    path_hashes.append(f"{field_name}:{file_hash}")
                except Exception:
                    # Skip files that can't be hashed (e.g., don't exist)
                    continue

        # Combine all hashes into a single path hash
        self.config_path_hash = "|".join(path_hashes)
        return self


class PathHashMixin(BaseModel):
    path_hash: str | None = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def set_dependency_hash(self) -> Self:
        """Calculate combined hash of all fields ending in '_path'."""
        path_hashes = []

        # Get all field names that end with '_path'
        dump = self.model_dump()
        for field_name in sorted(dump.keys()):
            field_value = dump[field_name]
            if field_name.endswith("_path") and field_value is not None:
                try:
                    file_hash = calculate_file_hash(field_value)
                    path_hashes.append(f"{field_name}:{file_hash}")
                except Exception:
                    # Skip files that can't be hashed (e.g., don't exist)
                    continue

        # Combine all hashes into a single path hash
        self.path_hash = "|".join(path_hashes)
        return self


class PromptConfig(PathHashMixin):
    model: str
    template_path: str
    examples: list[dict] = []

    rate_limit: int = 300
    max_retries: int = 10


class HTMLPromptConfig(PromptConfig):
    example_dirs: list[str] = []

    @model_validator(mode="after")
    def set_examples(self) -> Self:
        def map_image_path(example_dir: str, image_path: str) -> str:
            return os.path.join(example_dir, image_path)

        examples = []
        for example_dir in self.example_dirs:
            # load the yaml file from our assets/prompts/adt_examples directory
            example_path = os.path.join(example_dir, "example.yaml")

            # read the file as YAML
            example = yaml.safe_load(read_text_file(example_path))

            # remap the image path to the correct location
            example["page_image_path"] = map_image_path(example_dir, example["page_image_path"])
            example["section"]["parts"] = [
                {**part, "image_path": map_image_path(example_dir, part["image_path"])} if part.get("type") == "image" else part
                for part in example["section"]["parts"]
            ]
            example["response"]["html_path"] = map_image_path(example_dir, example["response"]["html_path"])
            example["response"]["content"] = read_text_file(example["response"]["html_path"])
            examples.append(example)

        self.examples = examples
        return self


class CropPromptConfig(PromptConfig):
    recrop_template_path: str | None = None
    recrops: int = 0


class QuizPromptConfig(PromptConfig):
    """
    Prompt config for generating quizzes from sections.
    """

    sections_per_quiz: int = 3


class RenderPromptConfig(PromptConfig):
    """Prompt config that also includes a template used to render the final output."""

    render_template_path: str


class TemplateRenderConfig(PathHashMixin):
    """Render config that only includes a template used to render the final output."""

    render_template_path: str


class PageRangeConfig(BaseModel):
    start: int = 0
    end: int = 0


class TemplateConfig(BaseModel):
    output_dir: str
