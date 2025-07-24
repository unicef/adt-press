import io
from typing import Self

import instructor
from banks import Prompt
from litellm import acompletion
from matplotlib import patches
from matplotlib import pyplot as plt
from pydantic import BaseModel, Field, model_validator

from adt_press.utils.file import cached_read_file, cached_read_template, calculate_file_hash, write_file
from adt_press.utils.image import CropCoordinates, Image, visualize_crop_extents
from adt_press.utils.pdf import Page

from .prompt import PromptConfig


class CropPromptConfig(PromptConfig):
    recrop_template_path: str | None = None
    recrop_template_hash: str | None = Field(default=None, exclude=True)
    recrops: int = 0

    @model_validator(mode="after")
    def set_recrop_template_hash(self) -> Self:
        if self.recrop_template_path:
            self.recrop_template_hash = calculate_file_hash(self.recrop_template_path)
        return self


class CropResponse(BaseModel):
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

    prompt = Prompt(cached_read_template(config.template_path))
    messages = [m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)]

    client = instructor.from_litellm(acompletion)
    response: CropResponse = await client.chat.completions.create(
        model=config.model,
        response_model=CropResponse,
        messages=messages,
        max_retries=3,
    )

    # if we have a recrop template
    if config.recrop_template_path:
        recrop_prompt = Prompt(cached_read_template(config.recrop_template_path))
        recrop = 0

        # and we want to recrop the image
        while recrop < config.recrops:
            cropped = visualize_crop_extents(cached_read_file(image.upath), response.top_left_x, response.top_left_y,
                                             response.bottom_right_x, response.bottom_right_y)
            cropped_upath = write_file(image.upath, cropped, "recrop")

            context = dict(
                crop_coordinates=response.model_dump(),
                cropped_upath=cropped_upath,
            )
            recrop_messages = [m.model_dump(exclude_none=True) for m in recrop_prompt.chat_messages(context)]
            messages = messages + recrop_messages
            response = await client.chat.completions.create(
                model=config.model,
                response_model=CropResponse,
                messages=messages,
                max_retries=3,
            )
            recrop += 1

    return CropCoordinates(
        top_left_x=response.top_left_x,
        top_left_y=response.top_left_y,
        bottom_right_x=response.bottom_right_x,
        bottom_right_y=response.bottom_right_y,
    )



