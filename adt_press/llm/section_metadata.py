# mypy: ignore-errors
import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import ValidationInfo, field_validator

from adt_press.models.config import LayoutType, PromptConfig
from adt_press.models.pdf import Page
from adt_press.models.section import PageSection, SectionMetadata
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file


class MetadataResponse(CleanTextBaseModel):
    background_color: str
    text_color: str
    layout_type: str
    reasoning: str

    @field_validator("layout_type")
    @classmethod
    def validate_layout_type(cls, v: str, info: ValidationInfo) -> str:
        layout_types = info.context.get("layout_types", [])
        if v not in layout_types:
            raise ValueError(f"layout_type '{v}' is not one of the valid layout types: {', '.join(layout_types)}")
        return v


async def get_section_metadata(
    config: PromptConfig, layout_types: dict[str, LayoutType], page: Page, section: PageSection, texts: list[str]
) -> SectionMetadata:
    context = dict(
        page=page,
        section=section,
        texts=texts,
        layout_types=layout_types,
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
        context={"layout_types": list(layout_types.keys())},
    )

    return SectionMetadata(
        section_id=section.section_id,
        background_color=response.background_color,
        text_color=response.text_color,
        layout_type=response.layout_type,
        reasoning=response.reasoning,
    )
