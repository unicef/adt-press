# mypy: ignore-errors
import os

from bs4 import BeautifulSoup, Comment, NavigableString

from adt_press.models.config import TemplateConfig
from adt_press.models.plate import PlateImage, PlateText


def replace_images(html_content: str, image_replacements: dict[str, PlateImage], text_replacements: dict[str, PlateText]) -> str:
    soup = BeautifulSoup(html_content, "html.parser")

    for tag in soup.find_all("img"):
        if tag.get("data-id") in image_replacements:
            img = image_replacements[tag["data-id"]]
            tag["src"] = img.image_path
            caption = text_replacements.get(img.caption_id)
            if caption:
                tag["alt"] = caption.text

    return str(soup)


def replace_texts(html_content: str, text_replacements: dict[str, PlateText]) -> str:
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
            if global_feedback and global_feedback not in section.descendants:
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
