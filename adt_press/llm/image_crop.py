import instructor
from banks import Prompt
from fsspec import open
from litellm import acompletion
from pydantic import BaseModel

from adt_press.utils.image import CropCoordinates, Image
from adt_press.utils.pdf import Page

from .prompt import PromptConfig


class CropResponse(BaseModel):
    top_left_x: int
    top_left_y: int
    bottom_right_x: int
    bottom_right_y: int


async def get_image_crop_coordinates(config: PromptConfig, page: Page, image: Image) -> CropCoordinates:
    template_path = config.template_path
    with open(template_path, "r") as template_file:
        template_content = template_file.read()

    context = dict(
        page=page,
        image=image,
        examples=config.examples,
    )

    prompt = Prompt(template_content)
    client = instructor.from_litellm(acompletion)
    response: CropResponse = await client.chat.completions.create(
        model=config.model,
        response_model=CropResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=3,
    )

    return CropCoordinates(
        top_left_x=response.top_left_x,
        top_left_y=response.top_left_y,
        bottom_right_x=response.bottom_right_x,
        bottom_right_y=response.bottom_right_y,
    )
