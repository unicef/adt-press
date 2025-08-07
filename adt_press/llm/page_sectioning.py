import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import BaseModel

from adt_press.data.image import ProcessedImage
from adt_press.data.pdf import Page
from adt_press.data.section import PageSection, PageSections, SectionType
from adt_press.data.text import PageText
from adt_press.llm.prompt import PromptConfig
from adt_press.utils.file import cached_read_text_file


class Section(BaseModel):
    section_id: str
    id: str
    section_type: SectionType


class SectionResponse(BaseModel):
    reasoning: str
    data: list[Section]


async def get_page_sections(config: PromptConfig, page: Page, images: list[ProcessedImage], texts: list[PageText]) -> PageSections:
    context = dict(
        page=page,
        images=[i.model_dump() for i in images],
        texts=[t.model_dump() for t in texts],
        examples=config.examples,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = instructor.from_litellm(acompletion)
    response: SectionResponse = await client.chat.completions.create(
        model=config.model,
        response_model=SectionResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
    )

    # convert our array to the more logical list of page sections
    sections = []
    section_by_id: dict[str, PageSection] = {}
    for s in response.data:
        section = section_by_id.get(s.section_id)
        if not section:
            section = PageSection(
                section_id=f"sec_{page.page_id}_s{s.section_id}",
                section_type=s.section_type,
            )
            section_by_id[s.section_id] = section
            sections.append(section)

        section.part_ids.append(s.id)

    return PageSections(
        page_id=page.page_id,
        sections=sections,
        reasoning=response.reasoning,
    )
