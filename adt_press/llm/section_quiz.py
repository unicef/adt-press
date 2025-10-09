# mypy: ignore-errors
import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import BaseModel, ValidationInfo, field_validator

from adt_press.models.config import LayoutType, PromptConfig, QuizPromptConfig
from adt_press.models.pdf import Page
from adt_press.models.section import PageSection, SectionMetadata, SectionQuiz
from adt_press.models.text import PageText, PageTextGroup
from adt_press.utils.file import cached_read_text_file


class QuizResponse(BaseModel):
    quiz: SectionQuiz
    reasoning: str

async def generate_quiz(
    config: QuizPromptConfig, sections: list[PageSection], text_groups_by_id: dict[str, PageTextGroup]) -> SectionQuiz:
    context = dict(
        sections=sections,
        text_groups=text_groups_by_id,
        examples=config.examples,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = instructor.from_litellm(acompletion)
    response: QuizResponse = await client.chat.completions.create(
        model=config.model,
        response_model=QuizResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
        context={},
    )

    quiz = response.quiz
    quiz.section_id = sections[0].section_id if sections else None

    return quiz
