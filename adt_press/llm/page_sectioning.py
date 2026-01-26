from banks import Prompt
from pydantic import AliasChoices, BaseModel, Field, ValidationInfo, field_validator

from adt_press.llm import get_instructor_client
from adt_press.models.config import PromptConfig, SectionType, SectionTypeName
from adt_press.models.ids import SectionID
from adt_press.models.image import ProcessedImage
from adt_press.models.pdf import Page
from adt_press.models.section import PageSection, PageSections
from adt_press.models.text import TextGroup
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file


class Section(BaseModel):
    section_type: str
    background_color: str
    text_color: str
    page_number: int | None
    part_ids: list[str]
    # Layout hint for HTML generation - describes how content should be arranged
    layout_hint: str = "stacked"


class SectionResponse(CleanTextBaseModel):
    reasoning: str
    sections: list[Section] = Field(validation_alias=AliasChoices("sections", "data"))

    @field_validator("sections")
    @classmethod
    def validate_section_ids(cls, v: list[Section], info: ValidationInfo) -> list[Section]:
        """Ensure all Section part IDs reference valid group or image IDs."""
        # Get valid IDs from context
        valid_ids = set()
        section_types: list[str] = []
        if info.context:
            # Add text IDs
            text_ids = info.context.get("text_ids", [])
            valid_ids.update(text_ids)

            # Add image IDs
            image_ids = info.context.get("image_ids", [])
            valid_ids.update(image_ids)

            section_types = info.context.get("section_types", [])

        # Validate each section's part IDs
        for i, section in enumerate(v):
            for part_id in section.part_ids:
                if valid_ids and part_id not in valid_ids:
                    raise ValueError(
                        f"Section at index {i} has invalid part_id='{part_id}'. Must be one of: {', '.join(sorted(valid_ids))}"
                    )
            if section.section_type not in section_types:
                raise ValueError(
                    f"Section at index {i} has invalid section_type='{section.section_type}'. Must be one of: {', '.join(sorted(section_types))}"
                )

        return v


async def get_page_sections(
    config: PromptConfig,
    section_types: dict[str, SectionType],
    spread_mode: bool,
    page: Page,
    images: list[ProcessedImage],
    groups: list[TextGroup],
) -> PageSections:
    context = dict(
        page=page,
        spread_mode=spread_mode,
        images=[i.model_dump() for i in images],
        texts=[dict(text_id=g.group_id, text=" ".join([t.text for t in g.texts])) for g in groups],
        examples=config.examples,
        section_types=section_types,
    )
    prompt = Prompt(cached_read_text_file(config.template_path))
    client = get_instructor_client()

    # Create validation context
    validation_context = {
        "text_ids": [t.group_id for t in groups],
        "image_ids": [i.image_id for i in images],
        "section_types": list(section_types.keys()),
    }

    response: SectionResponse = await client.chat.completions.create(
        model=config.model,
        response_model=SectionResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
        context=validation_context,
        timeout=config.timeout,
    )

    types_by_id = {st.name: st for st in section_types.values()}

    # convert response data directly to page sections
    sections = []
    for i, s in enumerate(response.sections):
        section = PageSection(
            section_id=SectionID(f"sec_{page.page_id}_s{i}"),
            section_type=types_by_id[SectionTypeName(s.section_type)],
            part_ids=s.part_ids.copy(),
            background_color=s.background_color,
            text_color=s.text_color,
            page_number=s.page_number,
            layout_hint=s.layout_hint,
        )
        sections.append(section)

    return PageSections(
        page_id=page.page_id,
        sections=sections,
        reasoning=response.reasoning,
    )
