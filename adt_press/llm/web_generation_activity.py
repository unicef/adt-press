# mypy: ignore-errors
from banks import Prompt
from bs4 import BeautifulSoup
from pydantic import ValidationInfo, field_validator

from adt_press.llm import get_instructor_client
from adt_press.models.config import HTMLPromptConfig, PromptConfig
from adt_press.models.plate import PlateImage, PlateSection, PlateText
from adt_press.models.web import RenderTextGroup, WebPage
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.html import extract_formatted_texts, validate_generated_html_data_ids
from adt_press.utils.languages import Language


class GenerationResponse(CleanTextBaseModel):
    reasoning: str
    content: str

    @field_validator("content")
    @classmethod
    def validate_html_data_ids(cls, v: str, info: ValidationInfo) -> str:
        """Sanitize and validate generated HTML content."""
        if not v or not v.strip():
            raise ValueError("Generated HTML content is empty.")

        # Get valid IDs from context
        text_ids = set()
        image_ids = set()
        section_type = None
        activity_rendering_enabled = True

        if info.context:
            text_ids.update(info.context.get("text_ids", []))
            image_ids.update(info.context.get("image_ids", []))
            section_type = info.context.get("section_type")
            activity_rendering_enabled = info.context.get("activity_rendering_enabled", True)

        # Use unified validation with activity-generated ID support
        return validate_generated_html_data_ids(
            v,
            text_ids=text_ids,
            image_ids=image_ids,
            section_type=section_type,
            activity_rendering_enabled=activity_rendering_enabled,
            allow_activity_generated_ids=True,
        )


async def generate_web_page_activity(
    render_strategy: str,
    config: PromptConfig,
    examples: list[str],
    section: PlateSection,
    groups: list[RenderTextGroup],
    texts: list[PlateText],
    images: list[PlateImage],
    language: Language,
    activity_prompts_config: dict[str, HTMLPromptConfig],
    activity_answers_prompts_config: dict[str, PromptConfig],
    activity_rendering_enabled: bool = True,
    retrieved_context: str = "",
    styleguide: str = "",
) -> WebPage:
    # Override config with activity-specific config if available
    section_type_key = section.section_type
    if section_type_key in activity_prompts_config:
        # Use the activity-specific config for this section type
        activity_config = activity_prompts_config[section_type_key]
        config = activity_config
        examples = activity_config.examples
    elif section_type_key.startswith("activity_"):
        # If it's an activity section but not in config, raise an error
        raise ValueError(
            f"No activity-specific prompt configuration found for section type: {section_type_key}. "
            f"Available activity types: {list(activity_prompts_config.keys())}"
        )

    context = dict(
        section=section,
        groups=[g.model_dump() for g in groups],
        texts=[t.model_dump() for t in texts],
        images=[i.model_dump() for i in images],
        language=language.name,
        examples=examples,
        retrieved_context=retrieved_context,
        styleguide=styleguide,
    )

    template_path = config.template_path
    prompt = Prompt(cached_read_text_file(template_path))

    client = get_instructor_client()

    # Create validation context for Pydantic
    validation_context = {
        "text_ids": [t.text_id for t in texts],
        "image_ids": [i.image_id for i in images],
        "section_type": section.section_type,
        "activity_rendering_enabled": activity_rendering_enabled,
    }

    messages = [m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)]

    response: GenerationResponse = await client.chat.completions.create(
        model=config.model,
        response_model=GenerationResponse,
        messages=messages,
        max_retries=config.max_retries,
        context=validation_context,
    )

    # Extract formatted texts with inline HTML tags preserved
    formatted_texts = extract_formatted_texts(response.content)

    # Extract activity-generated texts from the HTML (for activities only)
    soup = BeautifulSoup(response.content, "html.parser")
    known_ids = set(validation_context["text_ids"])
    generated_texts: list[PlateText] = []

    for element in soup.find_all(True):
        data_id = element.get("data-id")
        if not data_id or data_id in known_ids:
            continue

        # Only extract activity-generated texts (activity_gen_* prefix)
        if data_id.startswith("activity_gen_"):
            text_value = element.get_text(" ", strip=True)
            if text_value:
                generated_texts.append(
                    PlateText(
                        text_id=data_id,
                        text_type="activity_generated",
                        text=text_value,
                    )
                )
                known_ids.add(data_id)

    # Combine original text IDs with generated ones, preserving order
    combined_text_ids = list(dict.fromkeys([t.text_id for t in texts] + [t.text_id for t in generated_texts]))

    # Generate activity answers if config available
    activity_answers = {}
    activity_reasoning = ""

    if section_type_key in activity_answers_prompts_config:
        from adt_press.llm.activity_answers import generate_activity_answers

        answers_config = activity_answers_prompts_config[section_type_key]

        # Combine original texts with generated texts for context
        all_texts = texts + generated_texts

        answers_result = await generate_activity_answers(
            config=answers_config,
            section=section,
            texts=all_texts,
            content=response.content,
            language=language,
        )
        activity_answers = answers_result.answers
        activity_reasoning = answers_result.reasoning

    # The content is already sanitized and validated by the field_validator
    return WebPage(
        text_id=texts[0].text_id if texts else "",
        section_id=section.section_id,
        reasoning=response.reasoning,
        content=response.content,
        image_ids=[i.image_id for i in images],
        text_ids=combined_text_ids,
        render_strategy=render_strategy,
        generated_texts=generated_texts,
        formatted_texts=formatted_texts,
        activity_answers=activity_answers,
        activity_reasoning=activity_reasoning,
    )
