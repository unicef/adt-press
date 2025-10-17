import instructor
from banks import Prompt
from litellm import acompletion

from adt_press.models.config import PromptConfig
from adt_press.models.text import OutputText
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.languages import LANGUAGE_MAP


class TranslationResponse(CleanTextBaseModel):
    reasoning: str
    data: str


async def get_text_translation(
    config: PromptConfig, text_id: str, text_type: str, text: str, base_language_code: str, target_language_code: str
) -> OutputText:
    base_language = LANGUAGE_MAP[base_language_code]
    target_language = LANGUAGE_MAP[target_language_code]

    context = dict(
        base_language=base_language,
        target_language=target_language,
        text=text,
        examples=config.examples,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = instructor.from_litellm(acompletion)
    response: TranslationResponse = await client.chat.completions.create(
        model=config.model,
        response_model=TranslationResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
    )

    return OutputText(
        text_id=text_id, text_type=text_type, text=response.data, reasoning=response.reasoning, language_code=target_language_code
    )
