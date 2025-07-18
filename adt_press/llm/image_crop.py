import instructor
from banks import Prompt

from fsspec import open
from litellm import completion

from adt_press.utils.image import CropCoordinates, Image
from adt_press.utils.pdf import Page
from pydantic import BaseModel

from .prompt import PromptConfig


class CropResponse(BaseModel):
    crop_coordinates: CropCoordinates


def get_image_crop_coordinates(config: PromptConfig, page: Page, image: Image) -> CropCoordinates:
    template_path = config.template_path
    with open(template_path, "r") as template_file:
        template_content = template_file.read()

    context = dict(
        page=page,
        image=image,
        examples=config.examples,
    )

    prompt = Prompt(template_content)
    client = instructor.from_litellm(completion)
    response = client.chat.completions.create(
        model=config.model,
        response_model=CropResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=3,
    )

    return response.crop_coordinates
