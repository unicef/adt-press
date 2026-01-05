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
    activity = "activity"


class TextType(BaseModel):
    name: str
    description: str


class TextGroupType(BaseModel):
    name: str
    description: str


class SectionType(BaseModel):
    name: str
    description: str
    render_strategy: str = "html"


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
    timeout: int = 300


class SpeechProviderConfig(BaseModel):
    """Configuration for a specific TTS provider."""

    model: str
    voice: str = "auto"


class SpeechPromptConfig(PromptConfig):
    """Speech generation configuration with provider support."""

    provider: str = "auto"  # Default provider
    language_providers: dict[str, str] = {}  # Per-language provider overrides
    openai: SpeechProviderConfig = Field(default_factory=lambda: SpeechProviderConfig(model="gpt-4o-mini-tts", voice="auto"))
    azure: SpeechProviderConfig = Field(default_factory=lambda: SpeechProviderConfig(model="azure/speech/azure-tts", voice="auto"))
    format: str = "mp3"
    bit_rate: str = "64k"
    sample_rate: int = 24000

    def get_provider_for_language(self, language_code: str) -> str:
        """
        Get the appropriate provider for a specific language.

        Args:
            language_code: ISO language code (e.g., "en", "es", "si", "es-uy", "si-lk")

        Returns:
            Provider name ("openai" or "azure")
        """
        # Check exact match first (e.g., "es-uy")
        if language_code in self.language_providers:
            return self.language_providers[language_code]

        # If no exact match, try base language code (e.g., "es" from "es-uy")
        base_lang = language_code.split("-")[0]
        if base_lang in self.language_providers:
            return self.language_providers[base_lang]

        # Fall back to default provider
        if self.provider == "auto":
            return "openai"
        return self.provider

    def get_active_config(self, language_code: str | None = None) -> tuple[str, str]:
        """
        Get the active model and voice based on provider setting.

        Args:
            language_code: Optional ISO language code for per-language provider selection

        Returns:
            Tuple of (model, voice)
        """
        provider = self.provider if language_code is None else self.get_provider_for_language(language_code)

        if provider == "auto" or provider == "openai":
            return (self.openai.model, self.openai.voice)
        elif provider == "azure":
            return (self.azure.model, self.azure.voice)
        else:
            raise ValueError(f"Unknown speech provider: {provider}. Must be 'auto', 'openai', or 'azure'")


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


class MetadataPromptConfig(PromptConfig):
    """Prompt config for book metadata extraction with page range."""

    page_range: int = 3


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
