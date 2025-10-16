import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import BaseModel, ValidationInfo, field_validator

from adt_press.models.config import PromptConfig
from adt_press.models.image import ProcessedImage
from adt_press.models.pdf import Page
from adt_press.models.section import PageSection, PageSections, SectionType
from adt_press.models.text import PageTextGroup
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file


class Section(BaseModel):
    section_type: SectionType
    part_ids: list[str]


class SectionResponse(CleanTextBaseModel):
    reasoning: str
    data: list[Section]

    @field_validator("data")
    @classmethod
    def validate_section_ids(cls, v: list[Section], info: ValidationInfo) -> list[Section]:
        """Ensure all Section part IDs reference valid group or image IDs."""
        # Get valid IDs from context
        valid_ids = set()
        if info.context:
            # Add text IDs
            text_ids = info.context.get("text_ids", [])
            valid_ids.update(text_ids)

            # Add image IDs
            image_ids = info.context.get("image_ids", [])
            valid_ids.update(image_ids)

        # Validate each section's part IDs
        for i, section in enumerate(v):
            for part_id in section.part_ids:
                if valid_ids and part_id not in valid_ids:
                    raise ValueError(
                        f"Section at index {i} has invalid part_id='{part_id}'. Must be one of: {', '.join(sorted(valid_ids))}"
                    )

        return v


async def get_page_sections(config: PromptConfig, page: Page, images: list[ProcessedImage], groups: list[PageTextGroup]) -> PageSections:
    context = dict(
        page=page,
        images=[i.model_dump() for i in images],
        texts=[dict(text_id=g.group_id, text=" ".join([t.text for t in g.texts])) for g in groups],
        examples=config.examples,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = instructor.from_litellm(acompletion)

    # Create validation context
    validation_context = {
        "text_ids": [t.group_id for t in groups],
        "image_ids": [i.image_id for i in images],
    }

    response: SectionResponse = await client.chat.completions.create(
        model=config.model,
        response_model=SectionResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
        context=validation_context,
    )

    # convert response data directly to page sections
    sections = []
    for i, s in enumerate(response.data):
        section = PageSection(
            section_id=f"sec_{page.page_id}_s{i}",
            section_type=s.section_type,
            part_ids=s.part_ids.copy(),
        )
        sections.append(section)

    return PageSections(
        page_id=page.page_id,
        sections=sections,
        reasoning=response.reasoning,
    )
