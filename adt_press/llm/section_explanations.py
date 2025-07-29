import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import BaseModel

from adt_press.llm.prompt import PromptConfig
from adt_press.utils.file import cached_read_template
from adt_press.utils.image import ProcessedImage
from adt_press.utils.languages import LANGUAGE_MAP
from adt_press.utils.pdf import Page, PageSection, SectionExplanation


class ExplanationResponse(BaseModel):
    reasoning: str
    explanation: str


async def get_section_explanation(
    config: PromptConfig, page: Page, section: PageSection, texts: list[str], images: list[ProcessedImage], language_code: str
) -> SectionExplanation:
    language = LANGUAGE_MAP[language_code]

    context = dict(
        page=page,
        section=section,
        texts=texts,
        images=[img.model_dump() for img in images],
        language=language,
        examples=config.examples,
    )

    prompt = Prompt(cached_read_template(config.template_path))
    client = instructor.from_litellm(acompletion)
    response: ExplanationResponse = await client.chat.completions.create(
        model=config.model,
        response_model=ExplanationResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
    )

    return SectionExplanation(
        section_id=section.section_id,
        reasoning=response.reasoning,
        explanation=response.explanation,
    )
