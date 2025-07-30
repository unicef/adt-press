import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import BaseModel

from adt_press.llm.prompt import PromptConfig
from adt_press.utils.file import cached_read_template
from adt_press.utils.languages import LANGUAGE_MAP
from adt_press.utils.pdf import OutputText, PageText


class TranslationResponse(BaseModel):
    reasoning: str
    data: str


async def get_text_translation(config: PromptConfig, text: PageText, base_language_code: str, target_language_code: str) -> OutputText:
    base_language = LANGUAGE_MAP[base_language_code]
    target_language = LANGUAGE_MAP[target_language_code]

    context = dict(
        base_language=base_language,
        target_language=target_language,
        text=text.text,
        examples=config.examples,
    )

    prompt = Prompt(cached_read_template(config.template_path))
    client = instructor.from_litellm(acompletion)
    response: TranslationResponse = await client.chat.completions.create(
        model=config.model,
        response_model=TranslationResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
    )

    return OutputText(text_id=text.text_id, text=response.data, reasoning=response.reasoning, language_code=target_language_code)
