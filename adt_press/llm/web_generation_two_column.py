# mypy: ignore-errors
import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import BaseModel, ValidationInfo, field_validator

from adt_press.models.config import RenderPromptConfig
from adt_press.models.plate import PlateImage, PlateSection, PlateText
from adt_press.models.web import RenderTextGroup, WebPage
from adt_press.utils.encoding import CleanTextMixin
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


class GenerationResponse(CleanTextMixin,BaseModel):
    rows: list[Row]
    reasoning: str

    @field_validator("rows")
    @classmethod
    def validate_two_columns_layout(cls, v: list[Row], info: ValidationInfo) -> list[Row]:
        """Ensure valid layout rules and IDs for storybooks."""
        # Get valid IDs from context
        valid_ids = set()
        text_ids = []
        image_ids = []
        section_type = ""
        if info.context:
            text_ids = info.context.get("text_ids", [])
            image_ids = info.context.get("image_ids", [])
            section_type = info.context.get("section_type", "")
            valid_ids.update(text_ids)
            valid_ids.update(image_ids)

        seen_ids = set()

        # validate all parts in each row
        for row in v:
            # Allow either 1 column (image-only) or 2 columns (text + images)
            if len(row.columns) == 1:
                # Single column layout - allowed for image-only OR text-only
                if len(text_ids) > 0 and len(image_ids) > 0:
                    raise ValueError(
                        "Single column layout can only be used for pages with "
                        "ONLY images OR ONLY text, not both. "
                        f"Found text IDs: {text_ids} and image IDs: "
                        f"{image_ids}"
                    )
                # For text_only sections, require text and no images
                if section_type == "text_only":
                    if len(text_ids) == 0:
                        raise ValueError("text_only sections must have text content")
                    if len(image_ids) > 0:
                        raise ValueError("text_only sections should not have images")
                # Single column should span 5
                if row.columns[0].span != 5:
                    raise ValueError(f"Single column must have span 5, found {row.columns[0].span}.")
            elif len(row.columns) == 2:
                # Two column layout validation
                if row.columns[0].span != 3:
                    raise ValueError(f"Center column (images) must have span 3, found {row.columns[0].span}.")
                if row.columns[1].span != 2:
                    raise ValueError(f"Right column (text) must have span 2, found {row.columns[1].span}.")
            else:
                raise ValueError(f"Row must have either 1 column (image-only) or 2 columns (text+images), found {len(row.columns)}.")

            for column in row.columns:
                for part in column.parts:
                    if part in seen_ids:
                        raise ValueError(f"Duplicate part '{part}' found in row.")

                    if part not in valid_ids:
                        raise ValueError(f"Part '{part}' has invalid ID. Must be one of: {', '.join(sorted(valid_ids))}")

                    seen_ids.add(part)

        return v


async def generate_web_page_two_column(
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
        "section_type": section.section_type.name,
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
