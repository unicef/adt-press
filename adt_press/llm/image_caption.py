import instructor
from banks import Prompt
from litellm import acompletion
from pydantic import BaseModel

from adt_press.utils.file import cached_read_template
from adt_press.utils.image import Image, ImageCaption
from adt_press.utils.languages import LANGUAGE_MAP
from adt_press.utils.pdf import Page

from .prompt import PromptConfig


class CaptionResponse(BaseModel):
    caption: str
    reasoning: str


async def get_image_caption(config: PromptConfig, page: Page, image: Image, language_code: str) -> ImageCaption:
    language = LANGUAGE_MAP[language_code]

    context = dict(
        language_code=language_code,
        language=language,
        page=page,
        image=image,
        examples=config.examples,
    )

    prompt = Prompt(cached_read_template(config.template_path))
    client = instructor.from_litellm(acompletion)
    response: CaptionResponse = await client.chat.completions.create(
        model=config.model,
        response_model=CaptionResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
    )

    return ImageCaption(
        image_id=image.image_id,
        caption=response.caption,
        reasoning=response.reasoning,
    )
