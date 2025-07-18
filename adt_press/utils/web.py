import logging
import os

from pydantic import BaseModel


class TemplateConfig(BaseModel):
    output_dir: str
    template_dir: str


# given the passed in dict and template, render using jinja2
def render_template(config: TemplateConfig, template_path: str, context: dict) -> str:
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(config.template_dir))
    template = env.get_template(template_path)

    # write the output to a file named after the template
    output_path = config.output_dir + os.sep + template_path
    with open(output_path, "w") as f:
        f.write(template.render(context))

    logger = logging.getLogger(__name__)
    logger.info(f"Rendered template {template_path} to {output_path}")

    return str(output_path)
