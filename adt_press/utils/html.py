# mypy: ignore-errors
import os

from bs4 import BeautifulSoup, Comment, NavigableString

from adt_press.models.config import TemplateConfig
from adt_press.models.ids import ImageID, TextID
from adt_press.models.plate import PlateImage, PlateText


def replace_images(html_content: str, image_replacements: dict[ImageID, PlateImage], text_replacements: dict[TextID, PlateText]) -> str:
    soup = BeautifulSoup(html_content, "html.parser")

    for tag in soup.find_all("img"):
        if tag.get("data-id") in image_replacements:
            img = image_replacements[tag["data-id"]]
            tag["src"] = img.image_path
            caption = text_replacements.get(img.caption_id)
            if caption:
                tag["alt"] = caption.text

    return str(soup)


def replace_texts(html_content: str, text_replacements: dict[TextID, PlateText]) -> str:
    soup = BeautifulSoup(html_content, "html.parser")

    # NOTE: setting tag.string overwrites child nodes.
    # Assumes these tags are plain text.
    for tag in soup.find_all(
        [
            "h1",
            "h2",
            "h3",
            "p",
            "span",
        ]
    ):
        if tag.get("data-id") in text_replacements:
            tag.string = text_replacements[tag["data-id"]].text

    return str(soup)


def basename(text):
    return os.path.basename(text)


# given the passed in dict and template, render using jinja2


def sanitize_generated_html(html_content: str) -> str:
    """
    Strip outer document wrappers and duplicated shell elements from LLM HTML
    output. Preserves HTML comments.
    """
    soup = BeautifulSoup(html_content, "html.parser")

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

    ensure_required_activity_elements(root)

    fragments: list[str] = []
    for child in list(root.children):
        # Preserve HTML comments
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


def render_template_to_string(template_path: str, context: dict) -> str:
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader([".", "templates"]))
    env.filters["basename"] = basename
    template = env.get_template(template_path)

    return template.render(context)


def ensure_required_activity_elements(root) -> None:
    """Ensure required nodes exist for supported activities."""

    for section in root.find_all("section"):
        section_type = section.get("data-section-type")
        if section_type == "activity_sorting":
            # Look for an existing feedback element in this section
            feedback = section.find(id="feedback")
            if feedback:
                continue

            # Reuse a feedback element defined elsewhere if one exists
            global_feedback = root.find(id="feedback")
            if global_feedback and section not in global_feedback.parents:
                global_feedback.extract()
                section.append(global_feedback)
                continue

            new_feedback = root.new_tag("div")
            new_feedback["id"] = "feedback"
            new_feedback["class"] = ["mt-4", "text-center"]
            new_feedback["aria-live"] = "polite"
            section.append(new_feedback)

        elif section_type == "activity_open_ended_answer":
            inputs = section.select('input[type="text"], textarea')
            for index, field in enumerate(inputs, start=1):
                data_aria_id = field.get("data-aria-id")
                field_id = field.get("id")
                field_name = field.get("name")

                if data_aria_id or field_id or field_name:
                    continue

                generated_id = f"open-ended-input-{index}"
                field["data-aria-id"] = generated_id


# given the passed in dict and template, render using jinja2
def render_template(
    config: TemplateConfig,
    template_path: str,
    context: dict,
    output_name=None,
) -> str:
    # write the output to a file named after the template
    output_name = output_name if output_name else basename(template_path)
    output_path = config.output_dir + os.sep + output_name

    rendered_content = render_template_to_string(template_path, context)

    # Format HTML output for better readability
    if output_name.endswith(".html"):
        rendered_content = format_html(rendered_content)

    with open(output_path, "w") as f:
        f.write(rendered_content)

    return str(output_path)


def format_html(html: str) -> str:
    """Format HTML with proper indentation."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.prettify()


def extract_formatted_texts(html_content: str) -> dict[str, str]:
    """Extract formatted HTML text content from generated HTML by data-id.

    Returns a mapping of text_id -> inner_html (with inline formatting preserved).
    Example: {"text-1": "This is <b>bold</b> text"}
    """
    soup = BeautifulSoup(html_content, "html.parser")
    formatted_texts = {}

    # Find all elements with data-id
    for element in soup.find_all(attrs={"data-id": True}):
        data_id = element.get("data-id")
        if data_id:
            # Get inner HTML (preserves inline formatting tags)
            inner_html = "".join(str(child) for child in element.children)
            # Clean up and store
            formatted_texts[data_id] = inner_html.strip()

    return formatted_texts


def validate_generated_html_data_ids(
    html_content: str,
    text_ids: set[str],
    image_ids: set[str],
    section_type: str | None = None,
    activity_rendering_enabled: bool = True,
    allow_activity_generated_ids: bool = False,
) -> str:
    """Validate and sanitize generated HTML content.

    Args:
        html_content: The HTML content to validate
        text_ids: Set of valid text IDs
        image_ids: Set of valid image IDs
        section_type: The section type (e.g., "activity_multiple_choice")
        activity_rendering_enabled: Whether activity rendering is enabled
        allow_activity_generated_ids: Whether to allow activity_gen_* IDs

    Returns:
        The validated HTML content

    Raises:
        ValueError: If validation fails
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Strip document wrappers if LLM wrapped content in html/body tags
    if soup.body:
        # Extract just the body contents
        html_content = "".join(str(child) for child in soup.body.contents)
        soup = BeautifulSoup(html_content, "html.parser")

    if not soup.find(True):
        raise ValueError("Generated HTML does not contain any HTML elements.")

    # Validate text elements - STRICT: all elements with direct text need data-id
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

            # Allow activity-generated text IDs if permitted
            is_generated_activity_text = allow_activity_generated_ids and data_id.startswith("activity_gen_")

            if data_id not in text_ids and not is_generated_activity_text:
                raise ValueError(
                    f"HTML element '{element.name}' has invalid data-id='{data_id}'. Must be one of text IDs: {', '.join(sorted(text_ids))}"
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
        # Look for data-section-type on the section element first, then anywhere in the document
        data_section_type = section_element.get("data-section-type")
        if not data_section_type:
            # Try to find it on any element in the document
            element_with_attr = soup.find(attrs={"data-section-type": True})
            if element_with_attr:
                data_section_type = element_with_attr.get("data-section-type")
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

    return html_content


def contains_math_content(html: str) -> bool:
    """Check if HTML contains MathJax delimiters or math tags."""
    math_indicators = [
        r"\$",  # LaTeX inline: $...$
        r"\$$",  # LaTeX display: $$...$$
        r"\\\(",  # LaTeX inline: \(...\)
        r"\\\[",  # LaTeX display: \[...\]
        "<math",  # MathML tags
        "\\begin{",  # LaTeX environments
    ]
    return any(indicator in html for indicator in math_indicators)
