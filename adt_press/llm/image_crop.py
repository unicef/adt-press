import instructor
from banks import Prompt
from litellm import acompletion

from adt_press.models.config import CropPromptConfig
from adt_press.models.image import CropCoordinates, Image
from adt_press.models.pdf import Page
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_file, cached_read_text_file, write_file
from adt_press.utils.image import visualize_crop_extents


class CropResponse(CleanTextBaseModel):
    top_left_x: int
    top_left_y: int
    bottom_right_x: int
    bottom_right_y: int


async def get_image_crop_coordinates(config: CropPromptConfig, page: Page, image: Image) -> CropCoordinates:
    context = dict(
        page=page,
        image=image,
        examples=config.examples,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    messages = [m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)]

    client = instructor.from_litellm(acompletion)
    response: CropResponse = await client.chat.completions.create(
        model=config.model,
        response_model=CropResponse,
        messages=messages,
        max_retries=config.max_retries,
    )

    # if we have a recrop template
    if config.recrop_template_path:
        recrop_prompt = Prompt(cached_read_text_file(config.recrop_template_path))
        recrop = 0

        # and we want to recrop the image
        while recrop < config.recrops:
            cropped = visualize_crop_extents(
                cached_read_file(image.image_path),
                response.top_left_x,
                response.top_left_y,
                response.bottom_right_x,
                response.bottom_right_y,
            )
            cropped_path = write_file(image.image_path, cropped, "recrop")

            context = dict(
                crop_coordinates=response.model_dump(),
                cropped_path=cropped_path,
            )
            recrop_messages = [m.model_dump(exclude_none=True) for m in recrop_prompt.chat_messages(context)]
            messages = messages + recrop_messages
            response = await client.chat.completions.create(
                model=config.model,
                response_model=CropResponse,
                messages=messages,
                max_retries=config.max_retries,
            )
            recrop += 1

    return CropCoordinates(
        top_left_x=response.top_left_x,
        top_left_y=response.top_left_y,
        bottom_right_x=response.bottom_right_x,
        bottom_right_y=response.bottom_right_y,
    )
