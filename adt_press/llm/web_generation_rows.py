# mypy: ignore-errors
import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import BaseModel, ValidationInfo, field_validator

from adt_press.models.config import RenderPromptConfig
from adt_press.models.plate import PlateImage, PlateSection, PlateText
from adt_press.models.web import RenderTextGroup, WebPage
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.html import render_template_to_string
from adt_press.utils.languages import LANGUAGE_MAP


class Column(BaseModel):
    span: int
    background_color: str = "#ffffff"
    color: str = "#000000"
    parts: list[str]


class Row(BaseModel):
    columns: list[Column]


class GenerationResponse(BaseModel):
    reasoning: str
    rows: list[Row]

    @field_validator("rows")
    @classmethod
    def validate_html_data_ids(cls, v: list[Row], info: ValidationInfo) -> list[Row]:
        """Ensure all HTML nodes with text have data-id attributes that reference valid IDs."""
        # Get valid IDs from context
        valid_ids = set()
        if info.context:
            valid_ids.update(info.context.get("text_ids", []))
            valid_ids.update(info.context.get("image_ids", []))

        seen_ids = set()

        # validate all parts in each column
        for row in v:
            for column in row.columns:
                if len(column.parts) == 0:
                    raise ValueError(f"Row with columns {row.columns} has an empty column.")

                for part in column.parts:
                    if part in seen_ids:
                        raise ValueError(f"Duplicate part '{part}' found in row with columns {row.columns}.")

                    if part not in valid_ids:
                        raise ValueError(
                            f"Part '{part}' in row with columns {row.columns} has invalid ID. "
                            f"Must be one of: {', '.join(sorted(valid_ids))}"
                        )

                    seen_ids.add(part)

        return v


async def generate_web_page_rows(
    render_strategy: str,
    config: RenderPromptConfig,
    section: PlateSection,
    groups: list[RenderTextGroup],
    texts: list[PlateText],
    images: list[PlateImage],
    language_code: str,
) -> WebPage:
    language = LANGUAGE_MAP[language_code]

    context = dict(
        section=section,
        texts=[t.model_dump() for t in texts],
        images=[i.model_dump() for i in images],
        language=language,
    )

    template_path = config.template_path
    prompt = Prompt(cached_read_text_file(template_path))

    client = instructor.from_litellm(acompletion)

    # Create validation context for Pydantic
    validation_context = {
        "text_ids": [t.text_id for t in texts],
        "image_ids": [i.image_id for i in images],
    }

    response: GenerationResponse = await client.chat.completions.create(
        model=config.model,
        response_model=GenerationResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
        context=validation_context,
    )

    # Convert response rows to HTML
    content = render_template_to_string(
        config.render_template_path,
        {
            "section": section,
            "rows": response.rows,
            "texts": {t.text_id: t.model_dump() for t in texts},
            "images": {i.image_id: i for i in images},
        },
    )

    return WebPage(
        text_id=texts[0].text_id if texts else "",
        section_id=section.section_id,
        reasoning=response.reasoning,
        content=content,
        image_ids=[i.image_id for i in images],
        text_ids=[t.text_id for t in texts],
        render_strategy=render_strategy,
    )
