from banks import Prompt

from adt_press.llm import get_instructor_client
from adt_press.models.config import PromptConfig
from adt_press.models.ids import EasyReadID
from adt_press.models.text import EasyReadText, Text
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.languages import Language


class EasyReadResponse(CleanTextBaseModel):
    data: str
    reasoning: str


async def get_text_easy_read(output_language: Language, config: PromptConfig, text: Text) -> EasyReadText:
    context = dict(
        text=text,
        output_language=output_language.name,
        examples=config.examples,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = get_instructor_client()
    response: EasyReadResponse = await client.chat.completions.create(
        model=config.model,
        response_model=EasyReadResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
        timeout=config.timeout,
    )

    return EasyReadText(
        easy_read_id=EasyReadID(f"{text.text_id}_easy_read"),
        text_id=text.text_id,
        easy_read=response.data,
        reasoning=response.reasoning,
    )
