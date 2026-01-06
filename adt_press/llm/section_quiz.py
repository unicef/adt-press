# mypy: ignore-errors
import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import BaseModel, ValidationInfo, field_validator

from adt_press.models.config import QuizPromptConfig
from adt_press.models.section import PageSection, SectionQuiz
from adt_press.models.text import PageTextGroup
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.languages import Language


class Quiz(BaseModel):
    question: str
    options: list[dict]
    answer_index: int

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str, info: ValidationInfo) -> str:
        if len(v) > 200:
            raise ValueError(f"question '{v}' is too long")
        return v

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: list[dict], info: ValidationInfo) -> list[dict]:
        if not v:
            raise ValueError("options list is empty")
        if len(v) != 3:
            raise ValueError("quiz must include exactly 3 options")
        for option in v:
            text = option.get("text", "")
            explanation = option.get("explanation", "")
            if len(text) > 80:
                raise ValueError(f"option text '{text}' is too long")
            if len(explanation) > 400:
                raise ValueError(f"explanation '{explanation}' is too long")
            if not text:
                raise ValueError("option text is missing")
            if not explanation:
                raise ValueError("option explanation is missing")
        return v

    @field_validator("answer_index")
    @classmethod
    def validate_answer_index(cls, v: int, info: ValidationInfo) -> int:
        options = info.data.get("options", [])
        if v < 0 or v >= len(options):
            raise ValueError(f"answer_index '{v}' is out of range for options list of length {len(options)}")
        return v


class QuizResponse(BaseModel):
    quiz: Quiz
    reasoning: str


async def generate_quiz(
    config: QuizPromptConfig, language: Language, sections: list[PageSection], text_groups_by_id: dict[str, PageTextGroup]
) -> SectionQuiz:
    context = dict(
        sections=sections,
        text_groups=text_groups_by_id,
        examples=config.examples,
        language=language,
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

    option_texts = [option["text"] for option in response.quiz.options]
    option_explanations = [option["explanation"] for option in response.quiz.options]

    return SectionQuiz(
        quiz_id="qiz_" + after_section.section_id,
        section_id=after_section.section_id,
        question=response.quiz.question,
        options=option_texts,
        explanations=option_explanations,
        answer_index=response.quiz.answer_index,
        reasoning=response.reasoning,
    )
