import json
import os
import shutil

from hamilton.function_modifiers import cache

from adt_press.llm.web_generation_html import generate_web_page_html
from adt_press.llm.web_generation_rows import generate_web_page_rows
from adt_press.llm.web_generation_template import generate_web_page_template
from adt_press.llm.web_generation_two_column import generate_web_page_two_column
from adt_press.models.config import HTMLPromptConfig, LayoutType, RenderPromptConfig, RenderStrategy, TemplateConfig, TemplateRenderConfig
from adt_press.models.plate import Plate, PlateImage, PlateText
from adt_press.models.section import GlossaryItem
from adt_press.models.speech import SpeechFile
from adt_press.models.web import RenderTextGroup, WebPage
from adt_press.utils.html import render_template, replace_images, replace_texts
from adt_press.utils.sync import gather_with_limit, run_async_task
from adt_press.utils.web_assets import build_web_assets


def web_pages(
    plate_language_config: str,
    plate: Plate,
    default_model_config: str,
    layout_types_config: dict[str, LayoutType],
    render_strategy_config: str,
    render_strategies_config: dict[str, RenderStrategy],
) -> list[WebPage]:
    images_by_id = {img.image_id: img for img in plate.images}
    texts_by_id = {txt.text_id: txt for txt in plate.texts}
    groups_by_id = {grp.group_id: grp for grp in plate.groups}

    cached_configs = {}

    async def generate_pages():
        web_pages = []
        for section in plate.sections:
            texts: list[PlateText] = []
            images: list[PlateImage] = []
            groups: list[RenderTextGroup] = []

            for part_id in section.part_ids:
                if part_id.startswith("grp_"):
                    group = groups_by_id[part_id]
                    group_texts = []
                    for text_id in group.text_ids:
                        group_texts.append(texts_by_id[text_id])

                    texts.extend(group_texts)

                    groups.append(RenderTextGroup(group_id=group.group_id, group_type=group.group_type, texts=group_texts))
                elif part_id.startswith("img_"):
                    images.append(images_by_id[part_id])

            layout_type = layout_types_config.get(section.layout_type)
            if not layout_type:
                raise ValueError(f"Unknown layout type: {section.layout_type}")

            strategy_name = render_strategy_config
            if strategy_name == "dynamic":
                strategy_name = layout_type.render_strategy

            strategy = render_strategies_config.get(strategy_name)
            if not strategy:
                raise ValueError(f"Unknown render strategy: {strategy_name}")

            config = cached_configs.get(strategy_name)
            if not config:
                if "model" in strategy.config and strategy.config["model"] == "default":
                    strategy.config["model"] = default_model_config

                if strategy.render_type == "html":
                    config = HTMLPromptConfig.model_validate(strategy.config)
                elif strategy.render_type == "rows":
                    config = RenderPromptConfig.model_validate(strategy.config)
                elif strategy.render_type == "two_column":
                    config = RenderPromptConfig.model_validate(strategy.config)
                elif strategy.render_type == "template":
                    config = TemplateRenderConfig.model_validate(strategy.config)
                else:
                    raise ValueError(f"Unknown render strategy type: {strategy.render_type}")
                cached_configs[strategy_name] = config

            if strategy.render_type == "html":
                web_pages.append(
                    generate_web_page_html(strategy_name, config, config.examples, section, groups, texts, images, plate_language_config)
                )
            elif strategy.render_type == "rows":
                web_pages.append(generate_web_page_rows(strategy_name, config, section, groups, texts, images, plate_language_config))
            elif strategy.render_type == "two_column":
                web_pages.append(generate_web_page_two_column(strategy_name, config, section, groups, texts, images, plate_language_config))
            elif strategy.render_type == "template":
                web_pages.append(generate_web_page_template(strategy_name, config, section, groups, texts, images, plate_language_config))

        return await gather_with_limit(web_pages, 300)

    pages: list[WebPage] = run_async_task(generate_pages)

    image_urls = {
        img.image_id: PlateImage(image_id=img.image_id, image_path=f"images/{os.path.basename(img.image_path)}", caption_id=img.image_id)
        for img in plate.images
    }

    # for each page, remap images
    for page in pages:
        page.content = replace_images(page.content, image_urls, texts_by_id)

    return pages


@cache(behavior="recompute")
def package_adt_web(
    template_config: TemplateConfig,
    run_output_dir_config: str,
    pdf_title_config: str,
    plate_language_config: str,
    plate: Plate,
    plate_translations: dict[str, dict[str, str]],
    plate_glossary_translations: dict[str, list[GlossaryItem]],
    speech_files: dict[str, dict[str, SpeechFile]],
    web_pages: list[WebPage],
    strategy_config: dict[str, str],
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

    plate_images = {img.image_id: img for img in plate.images}
    plate_texts = {txt.text_id: txt for txt in plate.texts}
    sections_by_id = {section.section_id: section for section in plate.sections}

    for webpage_index, webpage in enumerate(web_pages):
        section = sections_by_id[webpage.section_id]

        # copy the images to the output directory
        images = {}
        for image_id in webpage.image_ids:
            image = plate_images[image_id]
            images[image_id] = PlateImage(image_id=image.image_id, image_path=f"images/{image_id}.png", caption_id=image.caption_id)

            shutil.copy(image.image_path, os.path.join(image_dir, f"{image_id}.png"))

        content = webpage.content
        content = replace_images(content, images, plate_texts)
        content = replace_texts(content, plate_texts)

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
        # speech files
        speeches = speech_files.get(language, dict[str, SpeechFile]())

        # Ensure speeches is always a dict (fix for when speech returns a list)
        if not isinstance(speeches, dict):
            speeches = dict[str, SpeechFile]()

        # create our language directory
        locale_dir = os.path.join(adt_dir, "content", "i18n", language)
        os.makedirs(locale_dir, exist_ok=True)

        # write our translated texts
        with open(os.path.join(locale_dir, "texts.json"), "w") as f:
            json.dump(translations, f, indent=2)

        audio_dir = os.path.join(locale_dir, "audio")
        os.makedirs(audio_dir, exist_ok=True)
        with open(os.path.join(locale_dir, "audios.json"), "w") as f:
            audio_map = dict[str, str]()
            for text_id, speech in speeches.items():
                filename = f"{speech.text_id}.mp3"
                audio_map[text_id] = filename

                # copy the audio file over
                shutil.copy(os.path.join(run_output_dir_config, speech.speech_path), os.path.join(audio_dir, filename))

            json.dump(audio_map, f, indent=2)

        # TODO: replace with real sign videos
        with open(os.path.join(locale_dir, "videos.json"), "w") as f:
            json.dump({}, f, indent=2)

        # write our glossary
        glossary = {
            i.word: dict(word=i.word, definition=i.definition, variations=i.variations, emoji="".join(i.emojis))
            for i in plate_glossary_translations[language]
        }
        with open(os.path.join(locale_dir, "glossary.json"), "w") as f:
            json.dump(glossary, f, indent=2)

    # copy our assets to the output directory
    assets_dir = os.path.join("assets", "web", "assets")
    shutil.copytree(assets_dir, os.path.join(adt_dir, "assets"), dirs_exist_ok=True)

    # write our config file
    render_template(
        template_config,
        "config.json",
        dict(
            languages=list(plate_translations.keys()),
            default_language=default_language,
            book_title=pdf_title_config,
            config=strategy_config,
        ),
        output_name="adt/assets/config.json",
    )

    # copy Makefile in
    makefile_path = os.path.join("assets", "web", "utils", "Makefile")
    shutil.copy(makefile_path, os.path.join(adt_dir, "Makefile"))

    # copy package.json in
    package_path = os.path.join("assets", "web", "utils", "package.json")
    shutil.copy(package_path, os.path.join(adt_dir, "package.json"))

    # copy tailwind.config.js in
    tailwind_path = os.path.join("assets", "web", "utils", "tailwind.config.js")
    shutil.copy(tailwind_path, os.path.join(adt_dir, "tailwind.config.js"))

    build_web_assets(run_output_dir_config)

    return "done"
