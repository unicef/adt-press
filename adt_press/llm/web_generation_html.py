# mypy: ignore-errors
import re

import instructor
from banks import Prompt
from bs4 import BeautifulSoup
from bs4.element import Doctype
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
        """Ensure nodes with inline text declare valid data-id attributes."""
        if not v or not v.strip():
            raise ValueError("Generated HTML content is empty.")

        soup = BeautifulSoup(v, "html.parser")

        if not soup.find(True):
            raise ValueError(
                "Generated HTML does not contain any HTML elements."
            )

        # Get valid IDs from context
        text_ids = set()
        image_ids = set()
        if info.context:
            text_ids.update(info.context.get("text_ids", []))
            image_ids.update(info.context.get("image_ids", []))
            section_type = info.context.get("section_type")
        else:
            section_type = None

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
                            "HTML element "
                            f"'{element.name}' contains text but is missing "
                            "required data-id attribute. "
                            f"Text content: '{direct_text[:50]}...'"
                        )
                    )

                if text_ids and data_id not in text_ids:
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
                        "Image element has invalid data-id="
                        f"'{data_id}'. Must be one of image IDs: "
                        f"{', '.join(sorted(image_ids))}"
                    )
                )

        # Ensure required structural elements exist
        container = soup.find("div", id="content")
        if not container:
            raise ValueError(
                "Generated HTML is missing the main <div id='content'> container."
            )

        container_classes = container.get("class", [])
        if "container" not in container_classes:
            raise ValueError(
                "The main content container must include the 'container' class."
            )

        sections = soup.find_all("section")
        if not sections:
            raise ValueError(
                "Generated HTML must include a <section> element."
            )

        if len(sections) != 1:
            raise ValueError(
                "Generated HTML must include exactly one <section> element."
            )

        section_element = sections[0]

        if section_type:
            data_section_type = section_element.get("data-section-type")
            if data_section_type != section_type:
                raise ValueError(
                    (
                        "Section data-section-type attribute is invalid. "
                        f"Expected '{section_type}', got "
                        f"'{data_section_type}'."
                    )
                )

            if section_type.startswith("activity_"):
                expected_role = "activity"
            else:
                expected_role = "article"
            role = section_element.get("role")
            if role != expected_role:
                raise ValueError(
                    (
                        "Section role attribute is invalid. Expected "
                        f"'{expected_role}', got '{role}'."
                    )
                )

        if not soup.find(attrs={"data-id": True}):
            raise ValueError(
                (
                    "Generated HTML must include at least one element with a "
                    "data-id attribute."
                )
            )

        return v


def sanitize_generated_html(html: str) -> str:
    """Strip outer document wrappers and remote scripts from generated HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove top-level doctypes that confuse downstream HTML injection.
    for element in list(soup.contents):
        if isinstance(element, Doctype):
            element.extract()

    # If a body node exists, return only its direct children to avoid nesting.
    if soup.body:
        fragment = "".join(str(child) for child in soup.body.contents)
        fragment = re.sub(
            r"<!DOCTYPE html>",
            "",
            fragment,
            flags=re.IGNORECASE,
        )
        fragment = re.sub(
            r"^\s*html\s*$",
            "",
            fragment,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        fragment_soup = BeautifulSoup(fragment, "html.parser")

        for element in list(fragment_soup.contents):
            if isinstance(element, Doctype):
                element.extract()

        for head in fragment_soup.find_all("head"):
            head.decompose()

        for wrapper in fragment_soup.find_all(["html", "body"]):
            wrapper.unwrap()

        cleaned = "".join(str(child) for child in fragment_soup.contents)

        return cleaned.strip()

    # Default to the cleaned soup when no explicit body is present.
    return str(soup).strip()


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
        "section_type": section.section_type.value,
    }

    messages = [
        m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)
    ]

    response: GenerationResponse = await client.chat.completions.create(
        model=config.model,
        response_model=GenerationResponse,
        messages=messages,
        max_retries=config.max_retries,
        context=validation_context,
    )

    sanitized_content = sanitize_generated_html(response.content)

    return WebPage(
        text_id=texts[0].text_id if texts else "",
        section_id=section.section_id,
        reasoning=response.reasoning,
        content=sanitized_content,
        image_ids=[i.image_id for i in images],
        text_ids=[t.text_id for t in texts],
        render_strategy=render_strategy,
    )
