import os
import shutil
from typing import Any

import structlog
from hamilton.function_modifiers import cache, config

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

logger = structlog.get_logger()


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

    # Check if activity generation is enabled by looking at activity_prompts_config
    activity_strategy_enabled = len(activity_prompts_config) > 0

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

            # Derive section type info early
            section_type_name = getattr(section.section_type, "name", str(section.section_type))
            is_activity_section = section_type_name.startswith("activity_")

            strategy_name = render_strategy_config
            if strategy_name == "dynamic":
                strategy_name = layout_type.render_strategy

            # Guard: detect and handle mismatched section/layout assignments
            corrected_strategy = None

            if is_activity_section and section.layout_type != "textbook_activity" and activity_strategy_enabled:
                # Activity with wrong layout - force to activity HTML rendering (only if activity_strategy=llm)
                corrected_strategy = render_strategies_config.get("activity")
                if corrected_strategy:
                    logger.warning(
                        "Layout mismatch corrected",
                        section_id=section.section_id,
                        section_type=section_type_name,
                        layout_type=section.layout_type,
                        corrected_to="activity",
                    )
                    strategy_name = "activity"
                    strategy = corrected_strategy
            elif is_activity_section and not activity_strategy_enabled:
                # Activity section but activity_strategy=none - treat as regular content
                if section.layout_type == "textbook_activity":
                    # Has activity layout but should be rendered as regular content
                    fallback_strategy_name = "html"
                else:
                    # Use the layout's render strategy
                    fallback_strategy_name = layout_type.render_strategy if layout_type.render_strategy != "activity" else "html"

                corrected_strategy = render_strategies_config.get(fallback_strategy_name)
                if corrected_strategy:
                    logger.info(
                        "Activity rendering disabled, using regular content strategy",
                        section_id=section.section_id,
                        section_type=section_type_name,
                        layout_type=section.layout_type,
                        using_strategy=fallback_strategy_name,
                    )
                    strategy_name = fallback_strategy_name
                    strategy = corrected_strategy
            elif not is_activity_section and section.layout_type == "textbook_activity":
                # Non-activity with activity layout - pick appropriate non-activity strategy
                if section_type_name in ("text_only", "boxed_text"):
                    fallback_strategy_name = "two_column"
                elif section_type_name in ("text_and_images", "novel_text_and_images"):
                    fallback_strategy_name = "html"
                else:
                    fallback_strategy_name = "html"

                corrected_strategy = render_strategies_config.get(fallback_strategy_name)
                if corrected_strategy:
                    logger.warning(
                        "Layout mismatch corrected",
                        section_id=section.section_id,
                        section_type=section_type_name,
                        layout_type=section.layout_type,
                        corrected_to=fallback_strategy_name,
                    )
                    strategy_name = fallback_strategy_name
                    strategy = corrected_strategy

            # Get strategy if not already set by correction above
            if not corrected_strategy:
                strategy = render_strategies_config.get(strategy_name)
                if not strategy:
                    raise ValueError(f"Unknown render strategy: {strategy_name}")

            specific_activity_config = activity_prompts_config.get(section_type_name)
            cache_key = f"{strategy_name}::{section_type_name}" if specific_activity_config else strategy_name
            config = cached_configs.get(cache_key)
            if not config:
                if "model" in strategy.config and strategy.config["model"] == "default":
                    strategy.config["model"] = default_model_config
                if strategy.render_type == "template":
                    config = TemplateRenderConfig.model_validate(strategy.config)
                elif strategy.render_type == "html":
                    if strategy_name == "activity" and is_activity_section and specific_activity_config:
                        config = specific_activity_config
                    else:
                        config = HTMLPromptConfig.model_validate(strategy.config)
                else:
                    raise ValueError(f"Unknown render strategy type: {strategy.render_type}")
                cached_configs[cache_key] = config

            if strategy.render_type == "html":
                if strategy_name == "activity":
                    if is_activity_section:
                        effective_strategy_name = specific_activity_config and section_type_name or "activity"
                    else:
                        effective_strategy_name = "text_only"
                else:
                    effective_strategy_name = section_type_name

                # Determine if this specific page should use activity rendering
                page_activity_rendering = activity_strategy_enabled and is_activity_section

                web_pages.append(
                    generate_web_page_html(
                        render_strategy=effective_strategy_name,
                        config=config,
                        examples=config.examples,
                        section=section,
                        groups=groups,
                        texts=texts,
                        images=images,
                        language_code=plate_language_config,
                        activity_rendering_enabled=page_activity_rendering,
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

    return pages


@config.when(activity_strategy="llm")
def activity_answers__llm(
    web_pages: list[WebPage],
    plate: Plate,
    activity_answers_prompts_config: dict[str, PromptConfig],
    plate_language_config: str,
) -> list[WebPage]:
    """Generate answers for activity sections using LLM."""
    activity_types = {
        "activity_sorting",
        "activity_multiple_choice",
        "activity_true_false",
        "activity_fill_in_the_blank",
        "activity_fill_in_a_table",
        "activity_matching",
    }

    async def generate_answers():
        answer_tasks = []
        section_by_id = {s.section_id: s for s in plate.sections}

        for page in web_pages:
            section = section_by_id.get(page.section_id)
            if section:
                section_type_name = getattr(section.section_type, "name", section.section_type)

                if section_type_name in activity_types:
                    # Include both original texts and activity-generated texts
                    section_texts = [t for t in plate.texts if t.text_id in page.text_ids]
                    section_texts.extend(page.generated_texts)
                    answer_config = activity_answers_prompts_config.get(section_type_name)

                    if not answer_config:
                        continue

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

        for page, answer_coro in answer_tasks:
            answer_response = await answer_coro
            page.activity_answers = answer_response.answers
            page.activity_reasoning = answer_response.reasoning

    run_async_task(generate_answers)
    return web_pages


@config.when(activity_strategy="none")
def activity_answers__none(
    web_pages: list[WebPage],
    plate: Plate,
    activity_answers_prompts_config: dict[str, PromptConfig],
    plate_language_config: str,
) -> list[WebPage]:
    """Skip activity answer generation."""
    return web_pages


def activity_generated_texts(activity_answers: list[WebPage]) -> dict[str, PlateText]:
    """Extract activity-generated texts from web pages after activity processing."""
    generated: dict[str, PlateText] = {}
    for page in activity_answers:
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
    activity_answers: list[WebPage],
    activity_generated_texts: dict[str, PlateText],
    strategy_config: dict[str, str],
) -> str:
    """Package ADT web content with activity answers."""
    web_pages = activity_answers  # Alias for compatibility
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
        dict(
            webpages=web_pages,
            texts=plate_texts,
            sections=sections_by_id,
        ),
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
