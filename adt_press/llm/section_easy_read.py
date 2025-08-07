import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import BaseModel

from adt_press.data.section import PageSection, SectionEasyRead
from adt_press.llm.prompt import PromptConfig
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.languages import LANGUAGE_MAP



class EasyReadResponse(BaseModel):
    data: str
    reasoning: str


async def get_section_easy_read(language_code: str, config: PromptConfig, section: PageSection, texts: list[str]) -> SectionEasyRead:
    output_language = LANGUAGE_MAP[language_code]

    context = dict(
        section=section,
        texts=texts,
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

    return SectionEasyRead(
        section_id=section.section_id,
        text=response.data,
        reasoning=response.reasoning,
    )
