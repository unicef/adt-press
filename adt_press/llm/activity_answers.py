# mypy: ignore-errors
import re

import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import Field, field_validator

from adt_press.models.config import PromptConfig
from adt_press.models.plate import PlateSection, PlateText
from adt_press.models.section import ActivityAnswer
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.languages import LANGUAGE_MAP


class ActivityAnswersResponse(CleanTextBaseModel):
    reasoning: str = Field(..., description="Brief explanation of answer determination")
    answers: dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary mapping activity item IDs to their correct answers",
    )

    @field_validator("answers", mode="before")
    @classmethod
    def ensure_answers_dict(cls, v):
        """Ensure answers is always a dict, never None."""
        if v is None:
            return {}
        return v


async def generate_activity_answers(
    config: PromptConfig,
    section: PlateSection,
    texts: list[PlateText],
    content: str,
    language_code: str,
) -> ActivityAnswersResponse:
    language = LANGUAGE_MAP[language_code]

    context = dict(
        section=dict(
            section_id=section.section_id,
            section_type=section.section_type.value,
        ),
        texts=[dict(text_id=t.text_id, text=t.text, text_type=t.text_type) for t in texts],
        activity_html=content,
        language=language,
        examples=[],  # Prevent Undefined error in templates that iterate over examples
    )

    template_path = config.template_path
    prompt = Prompt(cached_read_text_file(template_path))

    client = instructor.from_litellm(acompletion)

    response: ActivityAnswersResponse = await client.chat.completions.create(
        model=config.model,
        response_model=ActivityAnswersResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
    )

    # If LLM returned empty answers but HTML has input fields, extract keys and use empty strings
    if not response.answers:
        # Extract all data-activity-item values from HTML
        item_pattern = r'data-activity-item="([^"]+)"'
        item_keys = re.findall(item_pattern, content)

        if item_keys:
            # Build answers dict with all keys and empty string values
            response.answers = {key: "" for key in item_keys}

    return ActivityAnswer(
        section_id=section.section_id,
        answers=response.answers,
        reasoning=response.reasoning,
    )
