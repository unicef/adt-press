# mypy: ignore-errors
import os

from bs4 import BeautifulSoup

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

    # TODO: is this the right set of tags to replace?
    for tag in soup.find_all(["h1", "h2", "p", "span", "div"]):
        if tag.get("data-id") in text_replacements:
            tag.string = text_replacements[tag["data-id"]].text

    return str(soup)


def basename(text):
    return os.path.basename(text)


# given the passed in dict and template, render using jinja2
def render_template_to_string(template_path: str, context: dict) -> str:
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader([".", "templates"]))
    env.filters["basename"] = basename
    template = env.get_template(template_path)

    return template.render(context)


# given the passed in dict and template, render using jinja2
def render_template(config: TemplateConfig, template_path: str, context: dict, output_name=None) -> str:
    # write the output to a file named after the template
    output_name = output_name if output_name else basename(template_path)
    output_path = config.output_dir + os.sep + output_name
    with open(output_path, "w") as f:
        f.write(render_template_to_string(template_path, context))

    return str(output_path)
