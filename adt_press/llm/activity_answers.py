# mypy: ignore-errors
import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import field_validator

from adt_press.models.config import PromptConfig
from adt_press.models.plate import PlateSection, PlateText
from adt_press.models.section import ActivityAnswer
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.languages import LANGUAGE_MAP


class ActivityAnswersResponse(CleanTextBaseModel):
    reasoning: str
    answers: dict[str, str] = {}  # Default to empty dict if LLM doesn't provide

    @field_validator("answers")
    @classmethod
    def validate_answers_present(cls, v):
        """Ensure answers is never None - convert to empty dict."""
        if v is None:
            return {}
        return v


async def generate_activity_answers(
    config: PromptConfig,
    section: PlateSection,
    texts: list[PlateText],
    activity_html: str,
    language_code: str,
) -> ActivityAnswer:
    """
    Generate correct answers for an interactive activity.

    Args:
        config: Configuration containing model and template path
        section: The section metadata (includes section_type)
        texts: List of texts from the section for context
        activity_html: The generated HTML content of the activity
        language_code: Language code for the activity

    Returns:
        ActivityAnswer domain model with section_id, reasoning and answers dict
    """
    language = LANGUAGE_MAP[language_code]

    context = dict(
        section=section.model_dump(),
        texts=[t.model_dump() for t in texts],
        activity_html=activity_html,
        language=language,
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

    # Defensive check - ensure answers field is present
    if response.answers is None:
        raise ValueError(
            f"LLM failed to provide required 'answers' field for section {section.section_id}. Reasoning: {response.reasoning}"
        )

    return ActivityAnswer(
        section_id=section.section_id,
        answers=response.answers,
        reasoning=response.reasoning,
    )
