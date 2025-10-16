import instructor
from banks import Prompt
from litellm import acompletion

from adt_press.models.config import PromptConfig
from adt_press.models.section import GlossaryItem, PageSection, SectionGlossary
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.languages import LANGUAGE_MAP


class GlossaryResponse(CleanTextBaseModel):
    data: list[GlossaryItem]
    reasoning: str


async def get_section_glossary(language_code: str, config: PromptConfig, section: PageSection, texts: list[str]) -> SectionGlossary:
    output_language = LANGUAGE_MAP[language_code]

    context = dict(
        section=section,
        texts=texts,
        output_language=output_language,
        examples=config.examples,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = instructor.from_litellm(acompletion)
    response: GlossaryResponse = await client.chat.completions.create(
        model=config.model,
        response_model=GlossaryResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
    )

    return SectionGlossary(
        section_id=section.section_id,
        items=response.data,
        reasoning=response.reasoning,
    )
