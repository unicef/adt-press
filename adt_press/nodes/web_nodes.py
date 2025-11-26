import os
import shutil
from typing import Any

from hamilton.function_modifiers import cache

from adt_press.llm.activity_answers import generate_activity_answers
from adt_press.llm.web_generation_html import generate_web_page_html
from adt_press.llm.web_generation_template import generate_web_page_template
from adt_press.models.config import (
    HTMLPromptConfig,
    LayoutType,
    PromptConfig,
    RenderStrategy,
    TemplateConfig,
    TemplateRenderConfig,
)
from adt_press.models.plate import Plate, PlateImage, PlateText
from adt_press.models.section import GlossaryItem
from adt_press.models.speech import SpeechFile
from adt_press.models.web import RenderTextGroup, WebPage
from adt_press.utils.file import write_json_file
from adt_press.utils.html import render_template, replace_images, replace_texts
from adt_press.utils.image import compress_image_for_web
from adt_press.utils.sync import gather_with_limit, run_async_task
from adt_press.utils.web_assets import build_config_json, build_web_assets


def web_pages(
    plate_language_config: str,
    plate: Plate,
    default_model_config: str,
    layout_types_config: dict[str, LayoutType],
    render_strategy_config: str,
    render_strategies_config: dict[str, RenderStrategy],
    activity_prompts_config: dict[str, HTMLPromptConfig],
    activity_answers_prompts_config: dict[str, PromptConfig],
) -> list[WebPage]:
    images_by_id = {img.image_id: img for img in plate.images}
    texts_by_id = {txt.text_id: txt for txt in plate.texts}
    groups_by_id = {grp.group_id: grp for grp in plate.groups}

    cached_configs: dict[str, Any] = {}

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

            # Normalize section type to string for dict lookups
            section_type_name = getattr(section.section_type, "name", str(section.section_type))

            # Check if we have a specific activity config for this section type
            # Activity configs are keyed by string names like "activity_open_ended_answer"
            specific_activity_config = activity_prompts_config.get(section_type_name)

            # Cache key must use normalized string
            cache_key = f"{strategy_name}::{section_type_name}" if specific_activity_config else strategy_name

            config = cached_configs.get(cache_key)
            if not config:
                if "model" in strategy.config and strategy.config["model"] == "default":
                    strategy.config["model"] = default_model_config

                if strategy.render_type == "template":
                    config = TemplateRenderConfig.model_validate(strategy.config)
                elif strategy.render_type == "html":
                    # Special handling for activity sections
                    if strategy_name == "activity":
                        # Use specific activity config if available, otherwise fallback to config template_path
                        if specific_activity_config:
                            config = specific_activity_config
                        else:
                            config = HTMLPromptConfig.model_validate(strategy.config)
                    else:
                        config = HTMLPromptConfig.model_validate(strategy.config)
                else:
                    raise ValueError(f"Unknown render strategy type: {strategy.render_type}")
                cached_configs[cache_key] = config

            if strategy.render_type == "html":
                # For activities, use section type as strategy name to enable proper template selection
                effective_strategy_name = strategy_name
                if strategy_name == "activity":
                    # If we have a specific config, use the section type name
                    # Otherwise, fallback to "activity_other" for generic handling
                    if specific_activity_config:
                        effective_strategy_name = section_type_name
                    else:
                        effective_strategy_name = "activity_other"

                web_pages.append(
                    generate_web_page_html(
                        effective_strategy_name, config, config.examples, section, groups, texts, images, plate_language_config
                    )
                )
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

    # Generate answers for activity sections
    activity_types = {
        "activity_sorting",
        "activity_multiple_choice",
        # "activity_quiz",
        "activity_true_false",
        "activity_fill_in_the_blank",
        "activity_matching",
        # Note: activity_open_ended_answer and activity_fill_in_a_table are intentionally excluded - no predefined answers
    }

    async def generate_answers():
        answer_tasks = []
        section_by_id = {s.section_id: s for s in plate.sections}

        for page in pages:
            section = section_by_id.get(page.section_id)
            if section:
                section_type_name = getattr(section.section_type, "name", section.section_type)

                # Only generate answers for activity types in the allowed list
                if section_type_name in activity_types:
                    section_texts = [t for t in plate.texts if t.text_id in page.text_ids]
                    answer_config = activity_answers_prompts_config.get(section_type_name)
                    if not answer_config:
                        continue  # no answers for this activity type
                    answer_tasks.append(
                        (
                            page,
                            generate_activity_answers(
                                answer_config,
                                section,
                                section_texts,
                                page.content,
                                plate_language_config,
                            ),
                        )
                    )

        # Generate all answers in parallel
        for page, answer_coro in answer_tasks:
            answer_response = await answer_coro
            page.activity_answers = answer_response.answers

    run_async_task(generate_answers)

    return pages


def activity_generated_texts(web_pages: list[WebPage]) -> dict[str, PlateText]:
    generated: dict[str, PlateText] = {}
    for page in web_pages:
        for text in page.generated_texts:
            generated[text.text_id] = text
    return generated


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
    activity_generated_texts: dict[str, PlateText],
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
    plate_texts.update(activity_generated_texts)
    sections_by_id = {section.section_id: section for section in plate.sections}

    for webpage_index, webpage in enumerate(web_pages):
        section = sections_by_id[webpage.section_id]

        # copy the images to the output directory
        images = {}
        for image_id in webpage.image_ids:
            image = plate_images[image_id]
            optimized_name = compress_image_for_web(
                image.image_path,
                image_dir,
                image_id,
            )
            images[image_id] = PlateImage(
                image_id=image.image_id,
                image_path=os.path.join("images", optimized_name),
                caption_id=image.caption_id,
            )

        content = webpage.content
        content = replace_images(content, images, plate_texts)
        content = replace_texts(content, plate_texts)

        render_template(
            template_config,
            "webpage.html",
            dict(
                content=content,
                webpage=webpage,
                section=section,
                language=plate_language_config,
                webpage_number=webpage_index + 1,
                activity_answers=webpage.activity_answers,
            ),
            output_name=f"adt/{webpage.section_id}.html",
        )

    # copy our cover image if it exists
    if plate.cover_image_id:
        compress_image_for_web(
            plate_images[plate.cover_image_id].image_path,
            adt_dir,
            "cover",
        )

    # create our navigation directory
    nav_dir = os.path.join(adt_dir, "content", "navigation")
    os.makedirs(nav_dir, exist_ok=True)
    render_template(
        template_config,
        "nav.html",
        dict(webpages=web_pages, texts=plate_texts),
        output_name="adt/content/navigation/nav.html",
    )

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
        write_json_file(os.path.join(locale_dir, "texts.json"), translations)

        audio_dir = os.path.join(locale_dir, "audio")
        os.makedirs(audio_dir, exist_ok=True)
        audio_map = dict[str, str]()
        for text_id, speech in speeches.items():
            filename = f"{speech.text_id}.mp3"
            audio_map[text_id] = filename
            # copy the audio file over
            shutil.copy(
                os.path.join(run_output_dir_config, speech.speech_path),
                os.path.join(audio_dir, filename),
            )

        write_json_file(os.path.join(locale_dir, "audios.json"), audio_map)

        # TODO: replace with real sign videos
        write_json_file(os.path.join(locale_dir, "videos.json"), dict())

        # write our glossary
        glossary = {
            i.word: dict(
                word=i.word,
                definition=i.definition,
                variations=i.variations,
                emoji="".join(i.emojis),
            )
            for i in plate_glossary_translations[language]
        }
        write_json_file(os.path.join(locale_dir, "glossary.json"), glossary)

        write_json_file(os.path.join(locale_dir, "glossary.json"), glossary)
    # write our config file
    config_output_path = "adt/assets/config.json"
    config_dir = os.path.dirname(os.path.join(run_output_dir_config, config_output_path))
    os.makedirs(config_dir, exist_ok=True)

    build_config_json(
        template_config,
        run_output_dir_config,
        book_title=pdf_title_config,
        languages=list(plate_translations.keys()),
        default_language=default_language,
        strategy_config=strategy_config,
        output_subdir="adt",
    )

    build_web_assets(run_output_dir_config, list(plate_translations.keys()))

    return "done"
