# mypy: ignore-errors
from banks import Prompt
from bs4 import BeautifulSoup, Comment, NavigableString
from pydantic import ValidationInfo, field_validator

from adt_press.llm import get_instructor_client
from adt_press.models.config import PromptConfig
from adt_press.models.plate import PlateActivity, PlateImage, PlateSection, PlateText
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
        """Sanitize and validate generated HTML content."""
        if not v or not v.strip():
            raise ValueError("Generated HTML content is empty.")

        soup = BeautifulSoup(v, "html.parser")

        # Strip document wrappers if LLM wrapped content in html/body tags
        if soup.body:
            # Extract just the body contents
            v = "".join(str(child) for child in soup.body.contents)
            soup = BeautifulSoup(v, "html.parser")

        if not soup.find(True):
            raise ValueError("Generated HTML does not contain any HTML elements.")

        # Get valid IDs from context
        text_ids = set()
        image_ids = set()
        if info.context:
            text_ids.update(info.context.get("text_ids", []))
            image_ids.update(info.context.get("image_ids", []))
            section_type = info.context.get("section_type")
            # Check if activity rendering is enabled
            activity_rendering_enabled = info.context.get("activity_rendering_enabled", True)
        else:
            section_type = None
            activity_rendering_enabled = True

        # Validate text elements
        for element in soup.find_all(True):  # Find all HTML elements
            # Get direct text content, excluding nested elements and comments
            direct_text_nodes = []
            for child in element.children:
                # Skip HTML comments
                if isinstance(child, Comment):
                    continue
                # Only include NavigableString (text nodes), not nested tags
                if isinstance(child, NavigableString):
                    text = str(child).strip()
                    if text:  # Only non-empty text
                        direct_text_nodes.append(text)

            # Check if element has meaningful direct text content
            if direct_text_nodes:
                direct_text = " ".join(direct_text_nodes)
                data_id = element.get("data-id")
                if not data_id:
                    raise ValueError(
                        f"HTML element '{element.name}' contains text but is missing "
                        f"required data-id attribute. Text content: '{direct_text[:50]}...'"
                    )

                # Allow activity-generated text IDs (activity_gen_*) or known text IDs
                is_generated_activity_text = data_id.startswith("activity_gen_")

                if data_id not in text_ids and not is_generated_activity_text:
                    raise ValueError(
                        f"HTML element '{element.name}' has invalid "
                        f"data-id='{data_id}'. Must be one of text IDs: "
                        f"{', '.join(sorted(text_ids))}"
                    )

        # Validate image elements
        for img_element in soup.find_all("img"):
            data_id = img_element.get("data-id")
            if not data_id:
                raise ValueError(f"Image element is missing required data-id attribute. Image attributes: {dict(img_element.attrs)}")

            if data_id not in image_ids:
                raise ValueError(f"Image element has invalid data-id='{data_id}'. Must be one of image IDs: {', '.join(sorted(image_ids))}")

        # Ensure required structural elements exist
        container = soup.find("div", id="content")
        if not container:
            raise ValueError("Generated HTML is missing the main <div id='content'> container.")

        container_classes = container.get("class", [])
        if "container" not in container_classes:
            raise ValueError("The main content container must include the 'container' class.")

        sections = soup.find_all("section")
        if not sections:
            raise ValueError("Generated HTML must include a <section> element.")

        if len(sections) != 1:
            raise ValueError("Generated HTML must include exactly one <section> element.")

        section_element = sections[0]

        if section_type:
            data_section_type = section_element.get("data-section-type")
            if data_section_type != section_type:
                raise ValueError(f"Section data-section-type attribute is invalid. Expected '{section_type}', got '{data_section_type}'.")

            # Determine expected role based on section type AND activity rendering status
            if section_type.startswith("activity_") and activity_rendering_enabled:
                expected_role = "activity"
            else:
                expected_role = "article"

            role = section_element.get("role")
            if role != expected_role:
                raise ValueError(f"Section role attribute is invalid. Expected '{expected_role}', got '{role}'.")

        if not soup.find(attrs={"data-id": True}):
            raise ValueError("Generated HTML must include at least one element with a data-id attribute.")

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
    activity_rendering_enabled: bool = True,
    activity: PlateActivity | None = None,
) -> WebPage:
    language = LANGUAGE_MAP[language_code]

    context = dict(
        section=section,
        groups=[g.model_dump() for g in groups],
        texts=[t.model_dump() for t in texts],
        texts_by_id={t.text_id: t.model_dump() for t in texts},
        images=[i.model_dump() for i in images],
        activity_items=activity.items if activity else [],
        activity=activity.model_dump() if activity else None,
        language=language,
        examples=examples,
    )

    template_path = config.template_path
    prompt = Prompt(cached_read_text_file(template_path))

    client = get_instructor_client()

    # Create validation context for Pydantic
    validation_context = {
        "text_ids": [t.text_id for t in texts],
        "image_ids": [i.image_id for i in images],
        "section_type": section.section_type.value,
        "activity_rendering_enabled": activity_rendering_enabled,
    }

    messages = [m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)]

    response: GenerationResponse = await client.chat.completions.create(
        model=config.model,
        response_model=GenerationResponse,
        messages=messages,
        max_retries=config.max_retries,
        context=validation_context,
    )

    # Extract activity-generated texts from the HTML (for activities only)
    soup = BeautifulSoup(response.content, "html.parser")
    known_ids = set(validation_context["text_ids"])
    generated_texts: list[PlateText] = []

    for element in soup.find_all(True):
        data_id = element.get("data-id")
        if not data_id or data_id in known_ids:
            continue

        # Only extract activity-generated texts (activity_gen_* prefix)
        if data_id.startswith("activity_gen_"):
            text_value = element.get_text(" ", strip=True)
            if text_value:
                generated_texts.append(
                    PlateText(
                        text_id=data_id,
                        text_type="activity_generated",
                        text=text_value,
                    )
                )
                known_ids.add(data_id)

    # Combine original text IDs with generated ones, preserving order
    combined_text_ids = list(dict.fromkeys([t.text_id for t in texts] + [t.text_id for t in generated_texts]))

    # The content is already sanitized and validated by the field_validator
    return WebPage(
        text_id=texts[0].text_id if texts else "",
        section_id=section.section_id,
        reasoning=response.reasoning,
        content=response.content,
        image_ids=[i.image_id for i in images],
        text_ids=combined_text_ids,
        render_strategy=render_strategy,
        generated_texts=generated_texts,
    )
