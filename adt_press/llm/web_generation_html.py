# mypy: ignore-errors
import instructor
from banks import Prompt
from bs4 import BeautifulSoup
from litellm import acompletion
from pydantic import ValidationInfo, field_validator

from adt_press.models.config import PromptConfig
from adt_press.models.plate import PlateImage, PlateSection, PlateText
from adt_press.models.web import RenderTextGroup, WebPage
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.languages import LANGUAGE_MAP


class GenerationResponse(CleanTextBaseModel):
    reasoning: str
    content: str

    @field_validator("content")
    @classmethod
    def validate_html_data_ids(cls, v: str, info: ValidationInfo) -> str:
        """Ensure all HTML nodes with text have data-id attributes that reference valid IDs."""
        soup = BeautifulSoup(v, "html.parser")

        # Get valid IDs from context
        text_ids = set()
        image_ids = set()
        if info.context:
            text_ids.update(info.context.get("text_ids", []))
            image_ids.update(info.context.get("image_ids", []))

        # Validate text elements
        for element in soup.find_all(True):  # Find all HTML elements
            # Check if element has direct text content (not just whitespace)
            direct_text = "".join(element.find_all(string=True, recursive=False)).strip()

            if direct_text:
                data_id = element.get("data-id")
                if not data_id:
                    raise ValueError(
                        f"HTML element '{element.name}' contains text but is missing required data-id attribute. "
                        f"Text content: '{direct_text[:50]}...'"
                    )

                if text_ids and data_id not in text_ids:
                    raise ValueError(
                        f"HTML element '{element.name}' has invalid data-id='{data_id}'. "
                        f"Must be one of text IDs: {', '.join(sorted(text_ids))}"
                    )

        # Validate image elements
        for img_element in soup.find_all("img"):
            data_id = img_element.get("data-id")
            if not data_id:
                raise ValueError(f"Image element is missing required data-id attribute. Image attributes: {dict(img_element.attrs)}")

            if image_ids and data_id not in image_ids:
                raise ValueError(f"Image element has invalid data-id='{data_id}'. Must be one of image IDs: {', '.join(sorted(image_ids))}")

        return v


async def generate_web_page_html(
    render_strategy: str,
    config: PromptConfig,
    examples: list[str],
    section: PlateSection,
    groups: list[RenderTextGroup],
    texts: list[PlateText],
    images: list[PlateImage],
    language_code: str,
) -> WebPage:
    language = LANGUAGE_MAP[language_code]

    context = dict(
        section=section,
        groups=[g.model_dump() for g in groups],
        texts=[t.model_dump() for t in texts],
        images=[i.model_dump() for i in images],
        language=language,
        examples=examples,
    )

    template_path = config.template_path
    prompt = Prompt(cached_read_text_file(template_path))

    client = instructor.from_litellm(acompletion)

    # Create validation context for Pydantic
    validation_context = {
        "text_ids": [t.text_id for t in texts],
        "image_ids": [i.image_id for i in images],
    }

    response: GenerationResponse = await client.chat.completions.create(
        model=config.model,
        response_model=GenerationResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
        context=validation_context,
    )

    return WebPage(
        text_id=texts[0].text_id if texts else "",
        section_id=section.section_id,
        reasoning=response.reasoning,
        content=response.content,
        image_ids=[i.image_id for i in images],
        text_ids=[t.text_id for t in texts],
        render_strategy=render_strategy,
    )
