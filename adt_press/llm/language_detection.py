from banks import Prompt
from pydantic import field_validator

from adt_press.llm import get_instructor_client
from adt_press.models.config import PromptConfig
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.languages import LANGUAGE_MAP


class LanguageDetectionResponse(CleanTextBaseModel):
    language_code: str
    reasoning: str
    confidence: float | None = None

    @field_validator("language_code")
    @classmethod
    def validate_language_code(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in LANGUAGE_MAP:
            raise ValueError(f"Unsupported language code '{value}'")
        return normalized


async def detect_input_language(sample_text: str, config: PromptConfig) -> LanguageDetectionResponse:
    language_options = [
        {"code": code, "name": name}
        for code, name in sorted(LANGUAGE_MAP.items(), key=lambda item: item[1])
    ]

    context = dict(
        language_options=language_options,
        sample_text=sample_text,
        examples=config.examples,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = get_instructor_client()

    response: LanguageDetectionResponse = await client.chat.completions.create(
        model=config.model,
        response_model=LanguageDetectionResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
    )

    return response
