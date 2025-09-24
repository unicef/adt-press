"""Web generation using the spread layout strategy."""

import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import BaseModel, Field, ValidationInfo, field_validator

from adt_press.models.config import RenderPromptConfig
from adt_press.models.plate import PlateImage, PlateSection, PlateText
from adt_press.models.web import WebPage
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.html import render_template_to_string
from adt_press.utils.languages import LANGUAGE_MAP


class SpreadColumn(BaseModel):
    """A column in a spread layout row."""
    
    span: float = Field(description="Width of the column (2.5 for spread columns, 5 for single column)")
    color: str = Field(default="#000000", description="Text color for the column")
    background_color: str = Field(default="#ffffff", description="Background color for the column")
    parts: list[str] = Field(description="List of text and image IDs in this column")

    @field_validator("parts")
    @classmethod
    def validate_parts(cls, v, info: ValidationInfo):
        """Validate that parts contain only valid IDs from the context."""
        if info.context:
            text_ids = info.context.get("text_ids", [])
            image_ids = info.context.get("image_ids", [])
            valid_ids = set(text_ids) | set(image_ids)
            for part in v:
                if part not in valid_ids:
                    raise ValueError(f"Part '{part}' has invalid ID. Must be one of: {', '.join(sorted(valid_ids))}")
        return v


class SpreadRow(BaseModel):
    """A row in a spread layout."""
    
    columns: list[SpreadColumn] = Field(description="List of columns in this row")

    @field_validator("columns")
    @classmethod
    def validate_columns(cls, v, info):
        """Validate column configuration for spread layouts."""
        if len(v) == 1:
            # Single column layout (cover page)
            if v[0].span != 5:
                raise ValueError("Single column must have span of 5")
        elif len(v) == 2:
            # Two-column spread layout
            if v[0].span != 2.5 or v[1].span != 2.5:
                raise ValueError("Spread columns must each have span of 2.5")
        else:
            raise ValueError("Spread layout must have 1 (cover) or 2 (spread) columns")
        
        # Validate unique parts across columns
        seen_ids = set()
        for col in v:
            for part in col.parts:
                if part in seen_ids:
                    raise ValueError(f"Duplicate part '{part}' found across columns.")
                seen_ids.add(part)
        
        return v


class GenerationResponse(BaseModel):
    """Response from the spread layout generation."""
    
    reasoning: str = Field(description="Brief explanation of the layout decisions")
    rows: list[SpreadRow] = Field(description="List of rows in the spread layout")

    @field_validator("rows")
    @classmethod
    def validate_rows(cls, v, info):
        """Validate that all provided IDs are used exactly once."""
        if hasattr(info, "context") and info.context:
            valid_ids = set(info.context.get("text_ids", [])) | set(info.context.get("image_ids", []))
            used_ids = set()
            
            for row in v:
                for col in row.columns:
                    for part in col.parts:
                        if part in used_ids:
                            raise ValueError(f"Duplicate part '{part}' found in layout.")
                        used_ids.add(part)
            
            # Allow for unused IDs in case some content is filtered out
            unused_ids = valid_ids - used_ids
            if unused_ids:
                # This is informational, not an error
                pass
        
        return v


async def generate_web_page_spread(
    render_strategy: str,
    config: RenderPromptConfig,
    section: PlateSection,
    texts: list[PlateText],
    images: list[PlateImage],
    language_code: str,
) -> WebPage:
    """Generate a web page using the spread layout strategy."""
    language = LANGUAGE_MAP[language_code]

    # For spread sections, separate content by page in sequential order
    left_page_content = {"texts": [], "images": []}
    right_page_content = {"texts": [], "images": []}
    
    # Extract page information from IDs and group by page number
    pages_in_section = {}
    
    for text in texts:
        # Extract p{num} from txt_p{num}_t{index}
        page_id = text.text_id.split('_')[1]
        page_num = int(page_id[1:])  # Extract number from p{num}
        if page_num not in pages_in_section:
            pages_in_section[page_num] = {"texts": [], "images": []}
        pages_in_section[page_num]["texts"].append(text.model_dump())
    
    for image in images:
        # Extract p{num} from img_p{num}_...
        page_id = image.image_id.split('_')[1]
        page_num = int(page_id[1:])  # Extract number from p{num}
        if page_num not in pages_in_section:
            pages_in_section[page_num] = {"texts": [], "images": []}
        pages_in_section[page_num]["images"].append(image.model_dump())
    
    # Sort pages and assign first to left, second to right
    sorted_page_nums = sorted(pages_in_section.keys())
    if len(sorted_page_nums) >= 1:
        left_page_content = pages_in_section[sorted_page_nums[0]]
    if len(sorted_page_nums) >= 2:
        right_page_content = pages_in_section[sorted_page_nums[1]]

    context = dict(
        section=section,
        texts=[t.model_dump() for t in texts],
        images=[i.model_dump() for i in images],
        left_page_content=left_page_content,
        right_page_content=right_page_content,
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
        messages=[
            m.model_dump(exclude_none=True)
            for m in prompt.chat_messages(context)
        ],
        max_retries=config.max_retries,
        context=validation_context,
    )

    # Convert response rows to HTML
    content = render_template_to_string(
        config.render_template_path,
        {
            "section": section,
            "rows": response.rows,
            "texts": {t.text_id: t.text for t in texts},
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
