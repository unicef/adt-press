import instructor
from banks import Prompt
from litellm import acompletion

from adt_press.models.config import PromptConfig
from adt_press.models.text import EasyReadText, PageText
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.languages import LANGUAGE_MAP


class EasyReadResponse(CleanTextBaseModel):
    data: str
    reasoning: str


async def get_text_easy_read(language_code: str, config: PromptConfig, text: PageText) -> EasyReadText:
    output_language = LANGUAGE_MAP[language_code]

    context = dict(
        text=text,
        output_language=output_language,
        examples=config.examples,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = instructor.from_litellm(acompletion)
    response: EasyReadResponse = await client.chat.completions.create(
        model=config.model,
        response_model=EasyReadResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
    )

    return EasyReadText(
        easy_read_id=f"{text.text_id}_easy_read",
        text_id=text.text_id,
        easy_read=response.data,
        reasoning=response.reasoning,
    )
