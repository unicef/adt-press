import instructor
from banks import Prompt
from litellm import completion
from pydantic import BaseModel

from adt_press.utils.image import Image, ImageCaption
from adt_press.utils.languages import LANGUAGE_MAP
from adt_press.utils.pdf import Page

from .prompt import PromptConfig


class CaptionResponse(BaseModel):
    caption: ImageCaption


def get_image_caption(config: PromptConfig, page: Page, image: Image, language_code: str) -> ImageCaption:
    language = LANGUAGE_MAP[language_code]

    template_path = config.template_path
    with open(template_path, "r") as template_file:
        template_content = template_file.read()

    context = dict(
        language_code=language_code,
        language=language,
        page=page,
        image=image,
        examples=config.examples,
    )

    prompt = Prompt(template_content)
    client = instructor.from_litellm(completion)
    response: CaptionResponse = client.chat.completions.create(
        model=config.model,
        response_model=CaptionResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=3,
    )

    return response.caption
