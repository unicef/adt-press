# mypy: ignore-errors
import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import BaseModel, ValidationInfo, field_validator

from adt_press.models.config import QuizPromptConfig
from adt_press.models.section import PageSection, SectionQuiz
from adt_press.models.text import PageTextGroup
from adt_press.utils.encoding import starts_with_emoji
from adt_press.utils.file import cached_read_text_file


class QuizResponse(BaseModel):
    quiz: SectionQuiz
    reasoning: str


class Quiz(BaseModel):
    question: str
    options: list[str]
    explanations: list[str]
    answer_index: str

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str, info: ValidationInfo) -> str:
        if len(v) > 200:
            raise ValueError(f"question '{v}' is too long")
        if not starts_with_emoji(v):
            raise ValueError(f"question '{v}' does not start with an emoji")
        return v

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: list[str], info: ValidationInfo) -> list[str]:
        if not v:
            raise ValueError("options list is empty")
        if len(v) > 4:
            raise ValueError(f"options list '{v}' is too long")
        for option in v:
            if len(option) > 50:
                raise ValueError(f"option '{option}' is too long")
            if not starts_with_emoji(option):
                raise ValueError(f"option '{option}' does not start with an emoji")
        return v

    @field_validator("answer_index")
    @classmethod
    def validate_answer_index(cls, v: int, info: ValidationInfo) -> int:
        options = info.context.get("options", [])
        if v < 0 or v >= len(options):
            raise ValueError(f"answer_index '{v}' is out of range for options list of length {len(options)}")
        return v


async def generate_quiz(config: QuizPromptConfig, sections: list[PageSection], text_groups_by_id: dict[str, PageTextGroup]) -> SectionQuiz:
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

    after_section = sections[-1]

    return SectionQuiz(
        quiz_id="qiz_" + after_section.section_id,
        section_id=after_section.section_id,
        question=response.quiz.question,
        options=response.quiz.options,
        explanations=response.quiz.explanations,
        answer_index=response.quiz.answer_index,
        reasoning=response.reasoning,
    )
