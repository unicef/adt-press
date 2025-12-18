from banks import Prompt

from adt_press.llm import get_instructor_client
from adt_press.models.config import PromptConfig
from adt_press.models.section import GlossaryItem, PageSection, SectionGlossary
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.languages import Language


class GlossaryResponse(CleanTextBaseModel):
    data: list[GlossaryItem]
    reasoning: str


async def get_section_glossary(language: Language, config: PromptConfig, section: PageSection, texts: list[str]) -> SectionGlossary:
    context = dict(
        section=section,
        texts=texts,
        output_language=language.name,
        examples=config.examples,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = get_instructor_client()
    response: GlossaryResponse = await client.chat.completions.create(
        model=config.model,
        response_model=GlossaryResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
        timeout=config.timeout,
    )

    return SectionGlossary(
        section_id=section.section_id,
        items=response.data,
        reasoning=response.reasoning,
    )
