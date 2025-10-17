import instructor
from banks import Prompt
from litellm import acompletion

from adt_press.models.config import PromptConfig
from adt_press.models.pdf import Page
from adt_press.models.text import PageText, PageTextGroup, PageTexts, TextGroupType, TextType
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.logging import io_logger


class Text(CleanTextBaseModel):
    text_type: TextType
    text: str


class TextGroup(CleanTextBaseModel):
    group_type: TextGroupType
    texts: list[Text]


class TextResponse(CleanTextBaseModel):
    reasoning: str
    groups: list[TextGroup]


@io_logger(label="text_extraction")
async def get_page_text(output_dir: str, task_id: str, config: PromptConfig, page: Page) -> PageTexts:
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
        groups=[
            PageTextGroup(
                group_id=f"grp_p{page.page_number}_g{gi}",
                group_type=g.group_type,
                texts=[
                    PageText(text_id=f"txt_p{page.page_number}_g{gi}_t{ti}", text=t.text, text_type=t.text_type)
                    for ti, t in enumerate(g.texts)
                ],
            )
            for gi, g in enumerate(response.groups)
        ],
        reasoning=response.reasoning,
    )
