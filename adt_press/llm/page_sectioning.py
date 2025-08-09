import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import BaseModel, ValidationInfo, field_validator

from adt_press.models.config import PromptConfig
from adt_press.models.image import ProcessedImage
from adt_press.models.pdf import Page
from adt_press.models.section import PageSection, PageSections, SectionType
from adt_press.models.text import PageText
from adt_press.utils.file import cached_read_text_file


class Section(BaseModel):
    section_id: str
    id: str
    section_type: SectionType


class SectionResponse(BaseModel):
    reasoning: str
    data: list[Section]

    @field_validator("data")
    @classmethod
    def validate_section_ids(cls, v: list[Section], info: ValidationInfo) -> list[Section]:
        """Ensure all Section IDs reference valid text or image IDs."""
        # Get valid IDs from context
        valid_ids = set()
        if info.context:
            # Add text IDs
            text_ids = info.context.get("text_ids", [])
            valid_ids.update(text_ids)

            # Add image IDs
            image_ids = info.context.get("image_ids", [])
            valid_ids.update(image_ids)

        # Validate each section's ID
        for section in v:
            if valid_ids and section.id not in valid_ids:
                raise ValueError(
                    f"Section with section_id='{section.section_id}' has invalid id='{section.id}'. "
                    f"Must be one of: {', '.join(sorted(valid_ids))}"
                )

        return v


async def get_page_sections(config: PromptConfig, page: Page, images: list[ProcessedImage], texts: list[PageText]) -> PageSections:
    context = dict(
        page=page,
        images=[i.model_dump() for i in images],
        texts=[t.model_dump() for t in texts],
        examples=config.examples,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = instructor.from_litellm(acompletion)

    # Create validation context
    validation_context = {
        "text_ids": [t.text_id for t in texts],
        "image_ids": [i.image_id for i in images],
    }

    response: SectionResponse = await client.chat.completions.create(
        model=config.model,
        response_model=SectionResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
        context=validation_context,
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
