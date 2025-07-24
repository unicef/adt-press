import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import BaseModel

from adt_press.llm.prompt import PromptConfig
from adt_press.utils.file import cached_read_template
from adt_press.utils.pdf import Page, PageText, TextData


class TextResponse(BaseModel):
    reasoning: str
    data: list[TextData]


async def get_page_text(config: PromptConfig, page: Page) -> PageText:
    context = dict(
        page=page,
        examples=config.examples,
    )

    prompt = Prompt(cached_read_template(config.template_path))
    client = instructor.from_litellm(acompletion)
    response: TextResponse = await client.chat.completions.create(
        model=config.model,
        response_model=TextResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
    )

    return PageText(
        page_index=page.page_index,
        text=response.data,
        reasoning=response.reasonning,
    )
