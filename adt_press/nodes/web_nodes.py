import json
import os
import shutil

import yaml
from hamilton.function_modifiers import cache

from adt_press.llm.prompt import PromptConfig
from adt_press.llm.web_generation import generate_web_page
from adt_press.utils.file import read_text_file
from adt_press.utils.html import replace_images, replace_texts
from adt_press.utils.image import ProcessedImage
from adt_press.utils.pdf import OutputText, Page, PageSection, PageSections, PageText, WebPage
from adt_press.utils.sync import gather_with_limit, run_async_task
from adt_press.utils.web import TemplateConfig, render_template


@cache(behavior="recompute")
def web_generation_examples(web_generation_examples_config: list[str]) -> list[dict]:
    def map_image_path(example_dir: str, image_path: str) -> str:
        return os.path.join(example_dir, image_path)

    examples = []
    for example_dir in web_generation_examples_config:
        # load the yaml file from our assets/prompts/adt_examples directory
        example_path = os.path.join(example_dir, "example.yaml")

        # read the file as YAML
        example = yaml.safe_load(read_text_file(example_path))

        # remap the image path to the correct location
        example["page_image_upath"] = map_image_path(example_dir, example["page_image_path"])
        example["section"]["parts"] = [
            {**part, "image_upath": map_image_path(example_dir, part["image_path"])} if part.get("type") == "image" else part
            for part in example["section"]["parts"]
        ]
        example["response"]["html_upath"] = map_image_path(example_dir, example["response"]["html_path"])
        example["response"]["content"] = read_text_file(example["response"]["html_upath"])
        examples.append(example)

    return examples


def web_pages(
    output_language_config: str,
    pdf_pages: list[Page],
    filtered_sections_by_page_id: dict[str, PageSections],
    filtered_pdf_texts_by_id: dict[str, PageText],
    processed_images_by_id: dict[str, ProcessedImage],
    web_generation_prompt_config: PromptConfig,
    web_generation_examples: list[dict],
) -> list[WebPage]:
    async def generate_pages():
        web_pages = []
        for page in pdf_pages:
            page_sections = filtered_sections_by_page_id[page.page_id]
            for section in filter(lambda s: not s.is_pruned, page_sections.sections):
                texts = []
                images: list[ProcessedImage] = []

                for part_id in section.part_ids:
                    text = filtered_pdf_texts_by_id.get(part_id)
                    texts.extend([text] if text else [])
                    image = processed_images_by_id.get(part_id)
                    images.extend([image] if image else [])

                web_pages.append(
                    generate_web_page(
                        web_generation_prompt_config, web_generation_examples, page, section, texts, images, output_language_config
                    )
                )

        return await gather_with_limit(web_pages, web_generation_prompt_config.rate_limit)

    return run_async_task(generate_pages)


@cache(behavior="recompute")
def package_adt_web(
    template_config: TemplateConfig,
    output_dir_config: str,
    pdf_pages: list[Page],
    output_language_config: str,
    filtered_sections_by_section_id: dict[str, PageSection],
    processed_images_by_id: dict[str, ProcessedImage],
    output_pdf_texts_by_id: dict[str, OutputText],
    web_pages: list[WebPage],
) -> str:
    adt_dir = os.path.join(output_dir_config, "adt")
    # clear the output adt directory
    if os.path.exists(adt_dir):
        shutil.rmtree(adt_dir)

    os.makedirs(adt_dir)

    image_dir = os.path.join(adt_dir, "images")
    os.makedirs(image_dir, exist_ok=True)

    content_dir = os.path.join(adt_dir, "content")
    os.makedirs(content_dir, exist_ok=True)

    all_texts = {}

    for webpage_index, webpage in enumerate(web_pages):
        section = filtered_sections_by_section_id[webpage.section_id]

        # copy the images to the output directory
        images = {}
        for image_id in webpage.image_ids:
            image = processed_images_by_id[image_id]
            images[image_id] = image
            shutil.copy(image.crop.upath, os.path.join(image_dir, f"{image_id}.png"))

        # build our map of texts
        texts = {}
        for text_id in webpage.text_ids:
            texts[text_id] = output_pdf_texts_by_id[text_id].text
            all_texts[text_id] = output_pdf_texts_by_id[text_id].text

        content = webpage.content
        content = replace_images(content, images)
        content = replace_texts(content, texts)

        render_template(
            template_config,
            "webpage.html",
            dict(content=content, webpage=webpage, section=section, language=output_language_config, webpage_number=webpage_index + 1),
            output_name=f"adt/{webpage.section_id}.html",
        )

    # create our navigation directory
    nav_dir = os.path.join(adt_dir, "content", "navigation")
    os.makedirs(nav_dir, exist_ok=True)
    render_template(
        template_config, "nav.html", dict(webpages=web_pages, texts=output_pdf_texts_by_id), output_name="adt/content/navigation/nav.html"
    )

    # create our locale dir
    locale_dir = os.path.join(adt_dir, "content", "i18n", output_language_config)
    os.makedirs(locale_dir, exist_ok=True)

    # write our translated texts
    with open(os.path.join(locale_dir, "texts.json"), "w") as f:
        json.dump(all_texts, f, indent=2)

    # TODO: replace with TTS
    with open(os.path.join(locale_dir, "audios.json"), "w") as f:
        json.dump({}, f, indent=2)

    # TODO: replace with real sign videos
    with open(os.path.join(locale_dir, "videos.json"), "w") as f:
        json.dump({}, f, indent=2)

    # copy our assets to the output directory
    assets_dir = os.path.join("assets", "web", "assets")
    shutil.copytree(assets_dir, os.path.join(adt_dir, "assets"), dirs_exist_ok=True)

    # write our config file
    render_template(template_config, "config.json", {}, output_name="adt/assets/config.json")

    # copy tailwind in
    tailwind_path = os.path.join("assets", "web", "assets", "tailwind_output.css")
    shutil.copy(tailwind_path, os.path.join(content_dir, "tailwind_output.css"))

    return "done"
