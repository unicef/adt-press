from typing import Self
import PIL
import instructor
import io
from banks import Prompt
from litellm import acompletion
from matplotlib import patches, pyplot as plt
from pydantic import BaseModel, Field, model_validator

from adt_press.utils.image import CropCoordinates, Image
from adt_press.utils.pdf import Page
from adt_press.utils.file import cached_read_file, cached_read_template, calculate_file_hash, read_file, write_file

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
            cropped = generate_cropped_image(cached_read_file(image.upath), response)
            cropped_upath = write_file(image.upath, cropped, "recrop")

            context = dict(
                crop_coordinates=response.model_dump(),
                cropped_upath=cropped_upath,
            )
            recrop_messages = [m.model_dump(exclude_none=True) for m in recrop_prompt.chat_messages(context)]
            messages = messages + recrop_messages
            response: CropResponse = await client.chat.completions.create(
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


def generate_cropped_image(image_bytes: bytes, coords: CropResponse) -> bytes:
    im = PIL.Image.open(io.BytesIO(image_bytes))
    _, ax = plt.subplots(figsize=(12, 8), dpi=200)
    ax.imshow(im)
    x, y, x2, y2 = (
        coords.top_left_x,
        coords.top_left_y,
        coords.bottom_right_x,
        coords.bottom_right_y,
    )
    rect = patches.Rectangle(
        (x, y), x2 - x, y2 - y, linewidth=1, edgecolor="r", facecolor="r", alpha=0.2
    )
    ax.add_patch(rect)
    
    # Plot the top-left and bottom-right coordinates
    #ax.annotate(f"({x}, {y})", (x, y), color="blue", fontsize=6, ha="right")
    #ax.annotate(f"({x2}, {y2})", (x2, y2), color="blue", fontsize=6, ha="left")
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return buf.read()
