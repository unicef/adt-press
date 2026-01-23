import enum
import os
from typing import Any, NewType, Self

import yaml
from pydantic import BaseModel, Field, model_validator

from adt_press.utils.file import calculate_file_hash, read_text_file


class RenderType(str, enum.Enum):
    html = "html"
    rows = "rows"
    two_column = "two_column"
    template = "template"
    activity = "activity"


TextTypeName = NewType("TextTypeName", str)
TextGroupTypeName = NewType("TextGroupTypeName", str)
SectionTypeName = NewType("SectionTypeName", str)
RenderStrategyName = NewType("RenderStrategyName", str)


class TextType(BaseModel):
    name: TextTypeName
    description: str


class TextGroupType(BaseModel):
    name: TextGroupTypeName
    description: str


class SectionType(BaseModel):
    name: SectionTypeName
    description: str
    render_strategy: str = "html"


class RenderStrategy(BaseModel):
    name: RenderStrategyName
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
    languages: list[str] = []  # List of language codes this provider handles


class SpeechPromptConfig(PromptConfig):
    """Speech generation configuration with provider support."""

    provider: str = "dynamic"  # "dynamic" for language-based selection, or specific provider name
    default_provider: str = "openai"  # Fallback when dynamic mode can't find a match
    providers: dict[str, SpeechProviderConfig] = Field(default_factory=dict)
    format: str = "mp3"
    bit_rate: str = "64k"
    sample_rate: int = 24000
    voices_path: str = "config/voices.yaml"
    language_map: dict[str, str] = Field(default_factory=dict, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def parse_providers(cls, data: Any) -> Any:
        """Convert provider dicts to SpeechProviderConfig objects."""
        if isinstance(data, dict) and "providers" in data:
            providers = data.get("providers", {})
            if isinstance(providers, dict):
                # Convert each provider dict to SpeechProviderConfig
                parsed_providers: dict[str, SpeechProviderConfig] = {}
                for name, config in providers.items():
                    if isinstance(config, dict):
                        parsed_providers[name] = SpeechProviderConfig.model_validate(config)
                    elif isinstance(config, SpeechProviderConfig):
                        parsed_providers[name] = config
                data = dict(data)  # Make a copy
                data["providers"] = parsed_providers
        return data

    @model_validator(mode="after")
    def build_language_map(self) -> Self:
        """Build language -> provider map once during initialization."""
        self.language_map = {}
        for provider_name, provider_config in self.providers.items():
            for lang in provider_config.languages:
                self.language_map[lang] = provider_name
        return self

    def get_provider_for_language(self, language_code: str) -> str:
        """
        Get the appropriate provider for a specific language.

        Args:
            language_code: ISO language code (e.g., "en", "es", "si", "es-uy", "si-lk")

        Returns:
            Provider name (e.g., "openai", "azure", "elevenlabs", etc.)
        """
        # If provider is set to a specific provider (not "dynamic"), use it
        if self.provider != "dynamic":
            return self.provider

        # Check exact match first (e.g., "es-uy")
        if language_code in self.language_map:
            return self.language_map[language_code]

        # If no exact match, try base language code (e.g., "es" from "es-uy")
        base_lang = language_code.split("-")[0]
        if base_lang in self.language_map:
            return self.language_map[base_lang]

        # Fall back to default provider
        return self.default_provider

    def get_active_config(self, language_code: str | None = None) -> str:
        """
        Get the active model based on provider setting.

        Args:
            language_code: Optional ISO language code for per-language provider selection

        Returns:
            Model name string

        Raises:
            ValueError: If provider is not configured
        """
        # For non-dynamic mode without language_code, use the fixed provider
        if self.provider != "dynamic" and language_code is None:
            provider = self.provider
        elif language_code is not None:
            provider = self.get_provider_for_language(language_code)
        else:
            provider = self.default_provider

        if provider not in self.providers:
            raise ValueError(f"Provider '{provider}' not found in configured providers: {list(self.providers.keys())}")

        return self.providers[provider].model


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


class KnowledgeBaseConfig(BaseModel):
    """Configuration for RAG-based knowledge retrieval."""

    enabled: bool = False
    references_path: str = "assets/references"
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 5
    collection_name: str = "adt_references"

    # Which collections to index (subdirectories of references_path)
    collections: list[str] = Field(
        default_factory=lambda: ["curriculum", "entities", "pedagogy", "book_context"]
    )


class StyleguideConfig(BaseModel):
    """Configuration for styleguide full injection.

    Styleguides are injected in full (not via RAG) to ensure design consistency.
    They provide HTML/CSS patterns, color palettes, and layout guidelines.
    """

    enabled: bool = False
    styleguides_path: str = "assets/prompts/styleguides"
    name: str = "default"  # Which styleguide to use (maps to styleguide_{name}.md)

    def get_styleguide_path(self) -> str:
        """Get the full path to the selected styleguide file."""
        return os.path.join(self.styleguides_path, f"styleguide_{self.name}.md")
