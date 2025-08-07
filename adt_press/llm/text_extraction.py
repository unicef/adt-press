import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import BaseModel

from adt_press.llm.prompt import PromptConfig
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.pdf import ExtractedTextType, Page, PageText, PageTexts


class Data(BaseModel):
    text: str
    type: ExtractedTextType


class TextResponse(BaseModel):
    reasoning: str
    data: list[Data]


async def get_page_text(config: PromptConfig, page: Page) -> PageTexts:
    context = dict(
        page=page,
        examples=config.examples,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = instructor.from_litellm(acompletion)
    response: TextResponse = await client.chat.completions.create(
        model=config.model,
        response_model=TextResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
    )

    return PageTexts(
        page_id=page.page_id,
        texts=[PageText(text_id=f"txt_p{page.page_number}_t{i}", text=d.text, type=d.type) for i, d in enumerate(response.data)],
        reasoning=response.reasoning,
    )
