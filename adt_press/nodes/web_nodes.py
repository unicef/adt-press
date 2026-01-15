import hashlib
import os
import pickle
import json
import shutil
from typing import Any

import structlog
from hamilton.function_modifiers import cache
from omegaconf import OmegaConf

from adt_press.llm.web_generation_activity import generate_web_page_activity
from adt_press.llm.web_generation_edit import edit_web_page_with_llm
from adt_press.llm.web_generation_html import generate_web_page_html
from adt_press.llm.web_generation_quiz import generate_web_quiz
from adt_press.llm.web_generation_template import generate_web_page_template
from adt_press.models.config import (
    HTMLPromptConfig,
    PromptConfig,
    RenderStrategy,
    RenderStrategyName,
    SectionType,
    SectionTypeName,
    TemplateConfig,
    TemplateRenderConfig,
)
from adt_press.models.ids import ImageID, SectionID, TextID
from adt_press.models.plate import Plate, PlateImage, PlateText
from adt_press.models.section import GlossaryItem
from adt_press.models.speech import SpeechFile
from adt_press.models.web import RenderTextGroup, WebPage
from adt_press.utils.file import write_json_file
from adt_press.utils.html import contains_math_content, render_template, replace_images, replace_texts
from adt_press.utils.image import compress_image_for_web
from adt_press.utils.languages import Language, LanguageCode
from adt_press.utils.sync import gather_with_limit, run_async_task
from adt_press.utils.web_assets import build_config_json, build_web_assets

log = structlog.get_logger(__name__)


def web_pages_cache_key(
    plate_language: Language,
    plate: Plate,
    default_model_config: str,
    active_section_types_config: dict[SectionTypeName, SectionType],
    render_strategy_config: RenderStrategyName,
    render_strategies_config: dict[RenderStrategyName, RenderStrategy],
    activity_prompts_config: dict[str, HTMLPromptConfig],
    activity_answers_prompts_config: dict[str, PromptConfig],
) -> str:
    """
    Generate a cache key that invalidates when any dependency changes.
    
    This includes all parameters that affect web page generation except:
    - cached_web_pages (this is what we're caching)
    - regenerate_section_ids_config (editing-specific)
    - edit_sections_config (editing-specific)
    - run_output_dir_config (filesystem path)
    - web_edit_prompt_config (only affects editing)
    """
    # Collect all values that should invalidate cache when changed
    cache_data = {
        "plate_language": plate_language,
        "plate_content": plate,
        "default_model": default_model_config,
        "render_strategy": render_strategy_config,
        "render_strategies": render_strategies_config,
        "active_section_types": active_section_types_config,
        "activity_prompts": activity_prompts_config,
        "activity_answers_prompts": activity_answers_prompts_config,
    }
    
    # Generate deterministic hash using pickle (same as Hamilton's caching)
    cache_bytes = pickle.dumps(cache_data, protocol=pickle.HIGHEST_PROTOCOL)
    cache_hash = hashlib.sha256(cache_bytes).hexdigest()
    
    return cache_hash


@cache(behavior="recompute")
def cached_web_pages(
    run_output_dir_config: str,
    web_pages_cache_key: str,
) -> list[WebPage]:
    """
    Load all previously generated web pages from disk.
    
    This enables incremental regeneration and editing - returns empty list
    on first run, loads from web_pages.json on subsequent runs.
    
    Cache is automatically invalidated when upstream dependencies change
    (render strategies, prompts, models, etc.) by comparing cache keys.
    """
    web_pages_path = os.path.join(run_output_dir_config, "web_pages.json")
    cache_key_path = os.path.join(run_output_dir_config, "web_pages_cache_key.txt")
    
    if not os.path.exists(web_pages_path):
        log.info("no_cached_web_pages", reason="file_not_found")
        return []
    
    # Check if cache key matches - if not, invalidate cache
    if os.path.exists(cache_key_path):
        with open(cache_key_path, 'r') as f:
            stored_key = f.read().strip()
        
        if stored_key != web_pages_cache_key:
            log.info("cache_invalidated", reason="dependency_changed",
                    stored_key=stored_key[:8], current_key=web_pages_cache_key[:8])
            return []
    else:
        log.info("cache_invalidated", reason="no_cache_key")
        return []
    
    with open(web_pages_path, 'r') as f:
        pages_data = json.load(f)
    
    pages = [WebPage.model_validate(p) for p in pages_data]
    log.info("loaded_cached_web_pages", path=web_pages_path, count=len(pages), 
             section_ids=[p.section_id for p in pages[:5]], cache_key=web_pages_cache_key[:8])
    return pages


def web_pages(
    plate_language: Language,
    plate: Plate,
    default_model_config: str,
    active_section_types_config: dict[SectionTypeName, SectionType],
    render_strategy_config: RenderStrategyName,
    render_strategies_config: dict[RenderStrategyName, RenderStrategy],
    activity_prompts_config: dict[str, HTMLPromptConfig],
    activity_answers_prompts_config: dict[str, PromptConfig],
    cached_web_pages: list[WebPage],
    regenerate_sections_config: list[SectionID],
    edit_sections_config: dict[SectionID, str],
    run_output_dir_config: str,
    web_edit_prompt_config: HTMLPromptConfig,
    web_pages_cache_key: str,
) -> list[WebPage]:
    """
    Generate or update web pages for all sections.
    
    This function supports three modes:
    1. Full generation (default): Generate all pages from scratch
    2. Regeneration: Use cached pages, regenerate one section from scratch
    3. Editing: Use cached pages, edit one or more sections with LLM guidance
    
    The function always returns the complete set of pages and saves them to
    web_pages.json for use in subsequent runs.
    """
    images_by_id = {img.image_id: img for img in plate.images}
    texts_by_id: dict[TextID, PlateText] = {txt.text_id: txt for txt in plate.texts}
    groups_by_id = {grp.group_id: grp for grp in plate.groups}
    quizzes_by_section_id = {quiz.section_id: quiz for quiz in plate.quizzes}

    # Build lookup for cached pages by section_id
    cached_by_section_id = {page.section_id: page for page in cached_web_pages}
    
    # Determine which sections to regenerate vs use from cache
    regenerate_section_ids = set(regenerate_sections_config)
    if regenerate_section_ids:
        log.info("regenerating_sections", section_ids=list(regenerate_section_ids), count=len(regenerate_section_ids))
    
    # Track edits to apply
    edits_to_apply = edit_sections_config
    if edits_to_apply:
        log.info("editing_sections", section_ids=list(edits_to_apply.keys()), count=len(edits_to_apply))

    cached_configs: dict[str, Any] = {}

    async def generate_pages():
        # Separate lists for cached vs new/edited pages
        cached_pages_list = []
        async_tasks = []
        
        for section in plate.sections:
            section_id = section.section_id
            
            # Check if we should use cached version (unless regenerating or editing)
            if section_id in cached_by_section_id and section_id not in regenerate_section_ids and section_id not in edits_to_apply:
                log.debug("using_cached_web_page", section_id=section_id)
                cached_pages_list.append(cached_by_section_id[section_id])
                continue
            
            # Collect section content
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

            # Get section type configuration
            section_type_obj = active_section_types_config.get(section.section_type)
            if not section_type_obj:
                raise ValueError(f"Unknown section type: {section.section_type}")

            strategy_name = render_strategy_config
            if strategy_name == "dynamic":
                # Use section_type's render_strategy instead of layout_type's
                strategy_name = section_type_obj.render_strategy

            strategy = render_strategies_config.get(strategy_name)
            specific_activity_config = activity_prompts_config.get(section.section_type)
            cache_key = f"{strategy_name}::{section.section_type}" if specific_activity_config else strategy_name
            config = cached_configs.get(cache_key)
            if not config:
                if "model" in strategy.config and strategy.config["model"] == "default":
                    strategy.config["model"] = default_model_config
                if strategy.render_type == "html":
                    config = HTMLPromptConfig.model_validate(strategy.config)
                elif strategy.render_type == "activity":
                    config = HTMLPromptConfig.model_validate(strategy.config)
                elif strategy.render_type == "template":
                    config = TemplateRenderConfig.model_validate(strategy.config)
                else:
                    raise ValueError(f"Unknown render strategy type: {strategy.render_type}")
                cached_configs[strategy_name] = config

            # Check if this section should be edited
            if section_id in edits_to_apply:
                existing_page = cached_by_section_id.get(section_id)
                if not existing_page:
                    raise ValueError(f"Cannot edit section {section_id} - not found in cached pages")
                
                edit_instruction = edits_to_apply[section_id]
                log.info("editing_web_page", section_id=section_id, instruction=edit_instruction, 
                         original_strategy=existing_page.render_strategy)
                
                # Edit with LLM (works for any HTML content regardless of how it was originally generated)
                async_tasks.append(
                    edit_web_page_with_llm(
                        section_id=section_id,
                        existing_page=existing_page,
                        edit_instruction=edit_instruction,
                        section=section,
                        config=web_edit_prompt_config,
                        language=plate_language,
                    )
                )
            else:
                if strategy.render_type == "html":
                    async_tasks.append(
                        generate_web_page_html(strategy_name, config, config.examples, section, groups, texts, images, plate_language)
                    )
                elif strategy.render_type == "template":
                    async_tasks.append(generate_web_page_template(strategy_name, config, section, groups, texts, images, plate_language))
                elif strategy.render_type == "activity":
                    async_tasks.append(
                        generate_web_page_activity(
                            strategy_name,
                            config,
                            config.examples,
                            section,
                            groups,
                            texts,
                            images,
                            plate_language,
                            activity_prompts_config,
                            activity_answers_prompts_config,
                        )
                    )

            # should we insert a quiz after this section?
            quiz = quizzes_by_section_id.get(section.section_id)
            if quiz:
                quiz_section_id = f"{section.section_id}_quiz"
                
                # Check if cached quiz exists (unless we're regenerating this section)
                if quiz_section_id in cached_by_section_id and section.section_id not in regenerate_section_ids:
                    log.debug("using_cached_quiz", section_id=quiz_section_id)
                    cached_pages_list.append(cached_by_section_id[quiz_section_id])
                else:
                    texts: list[PlateText] = []
                    texts.append(texts_by_id[quiz.question_id])
                    for option_id in quiz.option_ids:
                        texts.append(texts_by_id[option_id])
                    for explanation_id in quiz.explanation_ids:
                        texts.append(texts_by_id[explanation_id])

                    strategy = render_strategies_config.get("section_quiz")
                    config = TemplateRenderConfig.model_validate(strategy.config)
                    async_tasks.append(generate_web_quiz("section_quiz", config, plate_language, quiz, texts))

        # Execute all async tasks and combine with cached pages
        new_pages = await gather_with_limit(async_tasks, 300) if async_tasks else []
        return cached_pages_list + new_pages

    pages: list[WebPage] = run_async_task(generate_pages)

    image_urls = {
        ImageID(img.image_id): PlateImage(
            image_id=img.image_id, image_path=f"images/{os.path.basename(img.image_path)}", caption_id=img.caption_id
        )
        for img in plate.images
    }

    # for each page, remap images
    for page in pages:
        page.content = replace_images(page.content, image_urls, texts_by_id)

    # Sort pages to match original section order (important when mixing cached and new pages)
    section_order: dict[SectionID, int] = {}
    page_index = 0
    for section in plate.sections:
        section_order[section.section_id] = page_index
        page_index += 1
        # Account for quiz pages that follow sections
        if section.section_id in quizzes_by_section_id:
            quiz_section_id = SectionID(f"{section.section_id}_quiz")
            section_order[quiz_section_id] = page_index
            page_index += 1
    
    pages.sort(key=lambda p: section_order.get(p.section_id, 999999))

    # Save web_pages.json and cache key for next run
    web_pages_path = os.path.join(run_output_dir_config, "web_pages.json")
    cache_key_path = os.path.join(run_output_dir_config, "web_pages_cache_key.txt")
    
    write_json_file(web_pages_path, [p.model_dump() for p in pages])
    log.info("saved_web_pages", path=web_pages_path, count=len(pages))
    
    # Save cache key to enable validation on next run
    with open(cache_key_path, 'w') as f:
        f.write(web_pages_cache_key)
    log.info("saved_cache_key", path=cache_key_path, key=web_pages_cache_key[:8])

    return pages


@cache(behavior="recompute")
def package_adt_web(
    template_config: TemplateConfig,
    run_output_dir_config: str,
    pdf_title_config: str,
    plate_language: Language,
    plate: Plate,
    plate_translations: dict[LanguageCode, dict[TextID, str]],
    plate_glossary_translations: dict[LanguageCode, list[GlossaryItem]],
    speech_files: dict[LanguageCode, dict[TextID, SpeechFile]],
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
    quizzes_by_section_id = {quiz.section_id: quiz for quiz in plate.quizzes}

    page_list = []
    has_math = False
    has_open_ended = False
    last_known_section_number: int | None = 1

    for webpage_index, webpage in enumerate(web_pages):
        section = sections_by_id.get(webpage.section_id)
        is_quiz_page = False
        if section is None:
            quiz = quizzes_by_section_id.get(webpage.section_id)
            if quiz:
                is_quiz_page = True
                section = sections_by_id.get(quiz.section_id)

        if section:
            last_known_section_number = section.page_number or last_known_section_number
            if section.section_type == "activity_open_ended_answer":
                has_open_ended = True
        else:
            log.warning("webpage references unknown section; skipping metadata fields", section_id=webpage.section_id)

        page_number = None
        if not is_quiz_page:
            if section:
                page_number = section.page_number or last_known_section_number
            else:
                page_number = last_known_section_number

        # copy the images to the output directory
        images = {}
        for image_id in webpage.image_ids:
            image = plate_images[image_id]
            optimized_name = compress_image_for_web(
                image.image_path,
                image_dir,
                image_id,
            )
            images[ImageID(image_id)] = PlateImage(
                image_id=image.image_id,
                image_path=os.path.join("images", optimized_name),
                caption_id=image.caption_id,
            )

        content = webpage.content
        content = replace_images(content, images, plate_texts)
        content = replace_texts(content, plate_texts)

        # Check if this specific page has math content
        page_has_math = contains_math_content(content)

        has_math = has_math or page_has_math

        render_template(
            template_config,
            "webpage.html",
            dict(
                content=content,
                webpage=webpage,
                section=section,
                language=plate_language.code,
                webpage_number=webpage_index + 1,
                activity_answers=webpage.activity_answers,
                has_math=page_has_math,
            ),
            output_name=f"adt/{webpage.section_id}.html",
        )

        # add to our page list
        page_entry: dict[str, str | int] = dict(
            section_id=webpage.section_id,
            href=f"{webpage.section_id}.html",
        )
        if page_number is not None:
            page_entry["page_number"] = page_number
        page_list.append(page_entry)

    # write our page list out
    write_json_file(os.path.join(adt_dir, "content", "pages.json"), page_list)

    # create and write our table of contents
    toc = []
    for chapter in plate.table_of_contents:
        if chapter.section_id in sections_by_id:
            toc.append(
                dict(
                    chapter_id=chapter.chapter_id,
                    section_id=chapter.section_id,
                    href=f"{chapter.section_id}.html",
                    title=plate_texts[TextID(chapter.chapter_id)].text,
                )
            )
    write_json_file(os.path.join(adt_dir, "content", "toc.json"), toc)

    # copy our cover image if it exists
    if plate.cover_image_id:
        compress_image_for_web(
            plate_images[ImageID(plate.cover_image_id)].image_path,
            adt_dir,
            "cover",
        )

    # create our navigation directory
    nav_dir = os.path.join(adt_dir, "content", "navigation")
    os.makedirs(nav_dir, exist_ok=True)
    render_template(
        template_config,
        "nav.html",
        dict(table_of_contents=plate.table_of_contents, texts=plate_texts),
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
            shutil.copy(os.path.join(run_output_dir_config, speech.speech_path), os.path.join(audio_dir, filename))

        write_json_file(os.path.join(locale_dir, "audios.json"), audio_map)

        # TODO: replace with real sign videos
        write_json_file(os.path.join(locale_dir, "videos.json"), dict())

        # write our glossary
        glossary = {
            i.word: dict(word=i.word, definition=i.definition, variations=i.variations, emoji="".join(i.emojis))
            for i in plate_glossary_translations[language]
        }

        write_json_file(os.path.join(locale_dir, "glossary.json"), glossary)

    build_config_json(
        template_config,
        run_output_dir_config,
        book_title=pdf_title_config,
        languages=list(plate_translations.keys()),
        default_language=default_language,
        strategy_config=strategy_config,
        output_subdir="adt",
    )

    build_web_assets(run_output_dir_config, list(plate_translations.keys()), has_math=has_math, has_open_ended=has_open_ended)

    return "done"
