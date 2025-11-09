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
from adt_press.utils.html import sanitize_generated_html
from adt_press.utils.languages import LANGUAGE_MAP


class GenerationResponse(CleanTextBaseModel):
    reasoning: str
    content: str

    @field_validator("content")
    @classmethod
    def validate_html_data_ids(cls, v: str, info: ValidationInfo) -> str:
        """Ensure text nodes include the required data-id attributes."""
        soup = BeautifulSoup(v, "html.parser")

        # Get valid IDs from context
        text_ids = set()
        image_ids = set()
        allowed_prefixes = []
        if info.context:
            text_ids.update(info.context.get("text_ids", []))
            image_ids.update(info.context.get("image_ids", []))
            allowed_prefixes = info.context.get(
                "allowed_new_text_id_prefixes",
                [],
            )

        # Validate text elements
        for element in soup.find_all(True):  # Find all HTML elements
            # Check if element has direct text content (not just whitespace)
            direct_text = "".join(
                element.find_all(string=True, recursive=False)
            ).strip()

            if direct_text:
                data_id = element.get("data-id")
                if not data_id:
                    raise ValueError(
                        (
                            f"HTML element '{element.name}' contains text but "
                            "is missing required data-id attribute. "
                            f"Text content: '{direct_text[:50]}...'"
                        )
                    )

                is_allowed_new_id = any(
                    data_id.startswith(prefix)
                    for prefix in allowed_prefixes
                )

                if (
                    text_ids
                    and data_id not in text_ids
                    and not is_allowed_new_id
                ):
                    raise ValueError(
                        (
                            f"HTML element '{element.name}' has invalid "
                            f"data-id='{data_id}'. Must be one of text IDs: "
                            f"{', '.join(sorted(text_ids))}"
                        )
                    )

        # Validate image elements
        for img_element in soup.find_all("img"):
            data_id = img_element.get("data-id")
            if not data_id:
                raise ValueError(
                    (
                        "Image element is missing required data-id attribute. "
                        f"Image attributes: {dict(img_element.attrs)}"
                    )
                )

            if image_ids and data_id not in image_ids:
                raise ValueError(
                    (
                        f"Image element has invalid data-id='{data_id}'. "
                        "Must be one of image IDs: "
                        f"{', '.join(sorted(image_ids))}"
                    )
                )

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
    generated_text_prefix = "activity_gen_"

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
        "allowed_new_text_id_prefixes": [generated_text_prefix],
    }

    response: GenerationResponse = await client.chat.completions.create(
        model=config.model,
        response_model=GenerationResponse,
        messages=[
            m.model_dump(exclude_none=True)
            for m in prompt.chat_messages(context)
        ],
        max_retries=config.max_retries,
        context=validation_context,
    )

    sanitized_content = sanitize_generated_html(response.content)

    soup = BeautifulSoup(sanitized_content, "html.parser")
    known_ids = set(validation_context["text_ids"])
    generated_texts: list[PlateText] = []

    for element in soup.find_all(True):
        data_id = element.get("data-id")
        if not data_id or data_id in known_ids:
            continue

        text_value = element.get_text(" ", strip=True)
        if not text_value:
            continue

        generated_texts.append(
            PlateText(
                text_id=data_id,
                text_type="activity_generated",
                text=text_value,
            )
        )
        known_ids.add(data_id)

    combined_text_ids = list(
        dict.fromkeys(
            [t.text_id for t in texts]
            + [t.text_id for t in generated_texts]
        )
    )

    return WebPage(
        text_id=texts[0].text_id if texts else "",
        section_id=section.section_id,
        reasoning=response.reasoning,
        content=sanitized_content,
        image_ids=[i.image_id for i in images],
        text_ids=combined_text_ids,
        render_strategy=render_strategy,
        generated_texts=generated_texts,
    )
