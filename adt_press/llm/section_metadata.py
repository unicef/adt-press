import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import BaseModel

from adt_press.llm.section_glossary import GlossaryResponse
from adt_press.models.config import PromptConfig
from adt_press.models.pdf import Page
from adt_press.models.section import GlossaryItem, PageSection, SectionGlossary, SectionLayoutType, SectionMetadata
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.languages import LANGUAGE_MAP


class MetadataResponse(BaseModel):
    background_color: str
    text_color: str
    layout_type: SectionLayoutType
    reasoning: str

async def get_section_metadata(config: PromptConfig, page: Page, section: PageSection, texts: list[str]) -> SectionMetadata:
    context = dict(
        page=page,
        section=section,
        texts=texts,
        images=[],
        examples=config.examples,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = instructor.from_litellm(acompletion)
    response: MetadataResponse = await client.chat.completions.create(
        model=config.model,
        response_model=MetadataResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
    )

    return SectionMetadata(
        section_id=section.section_id,
        background_color=response.background_color,
        text_color=response.text_color,
        layout_type=response.layout_type,
        reasoning=response.reasoning,
    )
