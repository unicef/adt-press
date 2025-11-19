from banks import Prompt
from pydantic import ValidationInfo, field_validator

from adt_press.models.config import PromptConfig
from adt_press.models.text import OutputText
from adt_press.llm import get_instructor_client
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.languages import LANGUAGE_MAP


class TextItem(CleanTextBaseModel):
    text_id: str
    text: str


class TranslationResponse(CleanTextBaseModel):
    reasoning: str
    translations: list[TextItem]

    @field_validator("translations")
    @classmethod
    def validate_all_texts_translated(cls, v: list[TextItem], info: ValidationInfo) -> list[TextItem]:
        """Ensure all requested texts were translated."""
        if not info.context:
            return v

        expected_text_ids = info.context.get("expected_text_ids", set())
        if not expected_text_ids:
            return v

        translated_ids = {item.text_id for item in v}
        missing_ids = expected_text_ids - translated_ids
        extra_ids = translated_ids - expected_text_ids

        if missing_ids:
            raise ValueError(f"Missing translations for text IDs: {sorted(missing_ids)}")
        if extra_ids:
            raise ValueError(f"Unexpected translations for text IDs: {sorted(extra_ids)}")

        return v


async def get_text_translation(
    config: PromptConfig,
    texts: list[tuple[str, str, str]],  # [(text_id, text_type, text)]
    base_language_code: str,
    target_language_code: str,
) -> list[OutputText]:
    """Translate one or more texts together to maintain context."""
    base_language = LANGUAGE_MAP[base_language_code]
    target_language = LANGUAGE_MAP[target_language_code]

    # Format texts for the prompt and collect expected IDs
    texts_for_prompt = [{"text_id": text_id, "text": text} for text_id, _, text in texts]
    expected_text_ids = {text_id for text_id, _, _ in texts}

    context = dict(
        base_language=base_language,
        target_language=target_language,
        texts=texts_for_prompt,
        examples=config.examples,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = get_instructor_client()

    # Create validation context
    validation_context = {
        "expected_text_ids": expected_text_ids,
    }

    response: TranslationResponse = await client.chat.completions.create(
        model=config.model,
        response_model=TranslationResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
        context=validation_context,
    )

    # Map back to OutputText objects
    text_type_map = {text_id: text_type for text_id, text_type, _ in texts}
    return [
        OutputText(
            text_id=translation.text_id,
            text_type=text_type_map[translation.text_id],
            text=translation.text,
            reasoning=response.reasoning,
            language_code=target_language_code,
        )
        for translation in response.translations
    ]
