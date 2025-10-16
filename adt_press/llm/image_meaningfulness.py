import instructor
from banks import Prompt
from litellm import acompletion

from adt_press.models.config import PromptConfig
from adt_press.models.image import Image, ImageMeaningfulness
from adt_press.models.pdf import Page
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file


class MeaningfulnessResponse(CleanTextBaseModel):
    is_meaningful: bool
    reasoning: str


async def get_image_meaningfulness(config: PromptConfig, page: Page, image: Image) -> ImageMeaningfulness:
    context = dict(
        page=page,
        image=image,
        examples=config.examples,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = instructor.from_litellm(acompletion)
    response: MeaningfulnessResponse = await client.chat.completions.create(
        model=config.model,
        response_model=MeaningfulnessResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
    )

    return ImageMeaningfulness(
        image_id=image.image_id,
        is_meaningful=response.is_meaningful,
        reasoning=response.reasoning,
    )
