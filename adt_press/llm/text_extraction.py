from banks import Prompt
from pydantic import ValidationInfo, field_validator

from adt_press.llm import get_instructor_client
from adt_press.models.config import PromptConfig
from adt_press.models.pdf import Page
from adt_press.models.text import PageText, PageTextGroup, PageTexts
from adt_press.models.config import TextType, TextTypeName, TextGroupType, TextGroupTypeName
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.languages import Language
from adt_press.utils.logging import io_logger


class Text(CleanTextBaseModel):
    text_type: TextTypeName
    text: str

    @field_validator("text_type")
    @classmethod
    def validate_text_type(cls, v: str, info: ValidationInfo) -> str:
        if info.context:
            valid_types = info.context.get("text_types", [])
            if valid_types and v not in valid_types:
                raise ValueError(
                    f"Invalid text_type='{v}'. Must be one of: {', '.join(sorted(valid_types))}"
                )
        return v


class TextGroup(CleanTextBaseModel):
    group_type: TextGroupTypeName
    texts: list[Text]

    @field_validator("group_type")
    @classmethod
    def validate_group_type(cls, v: str, info: ValidationInfo) -> str:
        if info.context:
            valid_types = info.context.get("text_group_types", [])
            if valid_types and v not in valid_types:
                raise ValueError(
                    f"Invalid group_type='{v}'. Must be one of: {', '.join(sorted(valid_types))}"
                )
        return v


class TextResponse(CleanTextBaseModel):
    reasoning: str
    groups: list[TextGroup]


@io_logger(label="text_extraction")
async def get_page_text(
    output_dir: str,
    task_id: str,
    config: PromptConfig,
    text_types: dict[str, TextType],
    text_group_types: dict[str, TextGroupType],
    page: Page,
    language: Language,
) -> PageTexts:
    context = dict(
        page=page,
        language=language,  # Add to context
        examples=config.examples,
        text_types=text_types,
        text_group_types=text_group_types,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = get_instructor_client()
    
    # Create validation context
    validation_context = {
        "text_types": list(text_types.keys()),
        "text_group_types": list(text_group_types.keys()),
    }
    
    response: TextResponse = await client.chat.completions.create(
        model=config.model,
        response_model=TextResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
        timeout=config.timeout,
        context=validation_context,
    )

    return PageTexts(
        page_id=page.page_id,
        groups=[
            PageTextGroup(
                group_id=f"grp_p{page.page_number}_g{gi}",
                group_type=g.group_type,
                texts=[
                    PageText(text_id=f"txt_p{page.page_number}_g{gi}_t{ti}", text=t.text, text_type=t.text_type)
                    for ti, t in enumerate(g.texts)
                ],
            )
            for gi, g in enumerate(response.groups)
        ],
        reasoning=response.reasoning,
    )
