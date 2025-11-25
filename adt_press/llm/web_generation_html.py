# mypy: ignore-errors
from banks import Prompt
from bs4 import BeautifulSoup, Comment, NavigableString
from pydantic import ValidationInfo, field_validator

from adt_press.llm import get_instructor_client
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
        allowed_prefixes = []
        if info.context:
            text_ids.update(info.context.get("text_ids", []))
            image_ids.update(info.context.get("image_ids", []))
            allowed_prefixes = info.context.get(
                "allowed_new_text_id_prefixes",
                [],
            )
            section_type = info.context.get("section_type")
        else:
            section_type = None

        # Validate text elements
        for element in soup.find_all(True):  # Find all HTML elements
            # Get direct text content, excluding HTML comments
            direct_text_nodes = []
            for child in element.children:
                # Skip comments - they're allowed
                if isinstance(child, Comment):
                    continue
                # Only include NavigableString (text) that's not a comment
                if isinstance(child, NavigableString) and not isinstance(child, Comment):
                    direct_text_nodes.append(str(child))

            direct_text = "".join(direct_text_nodes).strip()

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

                is_allowed_new_id = any(data_id.startswith(prefix) for prefix in allowed_prefixes)

                if text_ids and data_id not in text_ids and not is_allowed_new_id:
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
                raise ValueError((f"Image element is missing required data-id attribute. Image attributes: {dict(img_element.attrs)}"))

            if data_id not in image_ids:
                raise ValueError(
                    (f"Image element has invalid data-id='{data_id}'. Must be one of image IDs: {', '.join(sorted(image_ids))}")
                )

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
                raise ValueError((f"Section data-section-type attribute is invalid. Expected '{section_type}', got '{data_section_type}'."))

            if section_type.startswith("activity_"):
                expected_role = "activity"
            else:
                expected_role = "article"
            role = section_element.get("role")
            if role != expected_role:
                raise ValueError((f"Section role attribute is invalid. Expected '{expected_role}', got '{role}'."))

        if not soup.find(attrs={"data-id": True}):
            raise ValueError(("Generated HTML must include at least one element with a data-id attribute."))

        return v


def strip_section_stray_text(root) -> None:
    """Remove stray text nodes directly inside <section> tags."""
    for section in root.find_all("section"):
        for child in list(section.children):
            if isinstance(child, NavigableString):
                if child.strip():
                    # Remove any non-whitespace text directly in section
                    child.extract()


def sanitize_generated_html(html_content: str) -> str:
    """
    Strip outer document wrappers and duplicated shell elements from LLM HTML output.
    Preserves HTML comments.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # DO NOT remove comments - they're allowed now
    # (removed the comment stripping code)

    # Prefer <body> contents when present, then <html>, otherwise the soup root
    root = soup.body or soup.find("html") or soup

    # Remove nested body/html wrappers within the selected root
    for nested_body in list(root.find_all("body")):
        nested_body.unwrap()
    for nested_html in list(root.find_all("html")):
        nested_html.unwrap()

    # Drop interface/nav containers – the app injects them separately
    shell_ids = {"interface-container", "nav-container"}

    def is_shell(tag_id: str | None) -> bool:
        return bool(tag_id and tag_id in shell_ids)

    for disallowed in list(root.find_all(id=is_shell)):
        disallowed.decompose()

    strip_section_stray_text(root)

    fragments: list[str] = []
    for child in list(root.children):
        # Comments are now preserved
        if isinstance(child, Comment):
            fragments.append(f"<!--{child}-->")
            continue
        if isinstance(child, NavigableString):
            if not child.strip():
                continue
            fragments.append(str(child))
        else:
            fragments.append(str(child))

    fragment_html = "".join(fragments).strip()

    return fragment_html or html_content.strip()


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

    client = get_instructor_client()

    # Create validation context for Pydantic
    validation_context = {
        "text_ids": [t.text_id for t in texts],
        "image_ids": [i.image_id for i in images],
        "allowed_new_text_id_prefixes": [generated_text_prefix],
        "section_type": section.section_type.value,
    }

    response: GenerationResponse = await client.chat.completions.create(
        model=config.model,
        response_model=GenerationResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
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

    combined_text_ids = list(dict.fromkeys([t.text_id for t in texts] + [t.text_id for t in generated_texts]))

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
