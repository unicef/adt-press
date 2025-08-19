import json
import os
import shutil

import yaml
from hamilton.function_modifiers import cache

from adt_press.llm.web_row_generation import generate_web_page_from_rows
from adt_press.models.config import PromptConfig, TemplateConfig
from adt_press.models.plate import Plate, PlateImage, PlateText
from adt_press.models.web import WebPage
from adt_press.utils.file import read_text_file
from adt_press.utils.html import render_template, replace_images, replace_texts
from adt_press.utils.sync import gather_with_limit, run_async_task


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
    plate_language_config: str,
    plate: Plate,
    template_config: TemplateConfig,
    web_generation_prompt_config: PromptConfig,
    web_generation_examples: list[dict],
) -> list[WebPage]:
    images_by_id = {img.image_id: img for img in plate.images}
    texts_by_id = {txt.text_id: txt for txt in plate.texts}

    async def generate_pages():
        web_pages = []
        for section in plate.sections:
            texts: list[PlateText] = []
            images: list[PlateImage] = []

            for part_id in section.part_ids:
                text = texts_by_id.get(part_id)
                texts.extend([text] if text else [])
                image = images_by_id.get(part_id)
                images.extend([image] if image else [])

            web_pages.append(
                generate_web_page_from_rows(
                    template_config, web_generation_prompt_config, web_generation_examples, section, texts, images, plate_language_config
                )
            )

        return await gather_with_limit(web_pages, web_generation_prompt_config.rate_limit)

    pages: list[WebPage] = run_async_task(generate_pages)

    image_urls = {
        img.image_id: PlateImage(image_id=img.image_id, upath=f"images/{os.path.basename(img.upath)}", caption=img.caption)
        for img in plate.images
    }

    # for each page, remap images
    for page in pages:
        page.content = replace_images(page.content, image_urls)

    return pages


@cache(behavior="recompute")
def package_adt_web(
    template_config: TemplateConfig,
    run_output_dir_config: str,
    pdf_title_config: str,
    plate_language_config: str,
    plate: Plate,
    plate_translations: dict[str, dict[str, str]],
    web_pages: list[WebPage],
) -> str:
    default_language = list(plate_translations.keys())[0]

    adt_dir = os.path.join(run_output_dir_config, "adt")

    # clear the output adt directory
    if os.path.exists(adt_dir):
        shutil.rmtree(adt_dir)  # pragma: no cover

    os.makedirs(adt_dir)

    image_dir = os.path.join(adt_dir, "images")
    os.makedirs(image_dir, exist_ok=True)

    content_dir = os.path.join(adt_dir, "content")
    os.makedirs(content_dir, exist_ok=True)

    all_texts = {}
    plate_images = {img.image_id: img for img in plate.images}
    plate_texts = {txt.text_id: txt for txt in plate.texts}
    sections_by_id = {section.section_id: section for section in plate.sections}

    for webpage_index, webpage in enumerate(web_pages):
        section = sections_by_id[webpage.section_id]

        # copy the images to the output directory
        images = {}
        for image_id in webpage.image_ids:
            image = plate_images[image_id]
            images[image_id] = PlateImage(image_id=image.image_id, upath=f"images/{image_id}.png", caption=image.caption)
            shutil.copy(image.upath, os.path.join(image_dir, f"{image_id}.png"))

        # build our map of texts
        texts = {}
        for text_id in webpage.text_ids:
            texts[text_id] = plate_texts[text_id].text
            all_texts[text_id] = plate_texts[text_id].text

        content = webpage.content
        content = replace_images(content, images)
        content = replace_texts(content, texts)

        render_template(
            template_config,
            "webpage.html",
            dict(content=content, webpage=webpage, section=section, language=plate_language_config, webpage_number=webpage_index + 1),
            output_name=f"adt/{webpage.section_id}.html",
        )

    # create our navigation directory
    nav_dir = os.path.join(adt_dir, "content", "navigation")
    os.makedirs(nav_dir, exist_ok=True)
    render_template(template_config, "nav.html", dict(webpages=web_pages, texts=plate_texts), output_name="adt/content/navigation/nav.html")

    for language, translations in plate_translations.items():
        # create our language directory
        locale_dir = os.path.join(adt_dir, "content", "i18n", language)
        os.makedirs(locale_dir, exist_ok=True)

        # write our translated texts
        with open(os.path.join(locale_dir, "texts.json"), "w") as f:
            json.dump(translations, f, indent=2)

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
    render_template(
        template_config,
        "config.json",
        dict(languages=list(plate_translations.keys()), default_language=default_language, book_title=pdf_title_config),
        output_name="adt/assets/config.json",
    )

    # copy tailwind in
    tailwind_path = os.path.join("assets", "web", "assets", "tailwind_output.css")
    shutil.copy(tailwind_path, os.path.join(content_dir, "tailwind_output.css"))

    return "done"
