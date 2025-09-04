import json

from hamilton.function_modifiers import cache

from adt_press.llm.glossary_translation import get_glossary_translation
from adt_press.llm.text_translation import get_text_translation
from adt_press.models.config import PromptConfig
from adt_press.models.image import ImageCaption, ProcessedImage
from adt_press.models.pdf import Page
from adt_press.models.plate import Plate, PlateImage, PlateSection, PlateText
from adt_press.models.section import GlossaryItem, PageSections, SectionExplanation, SectionGlossary
from adt_press.models.text import EasyReadText, OutputText, PageTexts
from adt_press.utils.file import calculate_file_hash, write_text_file
from adt_press.utils.sync import gather_with_limit, run_async_task


def generated_plate(
    pdf_title_config: str,
    plate_language_config: str,
    pdf_pages: list[Page],
    filtered_sections_by_page_id: dict[str, PageSections],
    processed_images_by_id: dict[str, ProcessedImage],
    plate_output_texts_by_id: dict[str, OutputText],
    explanations_by_section_id: dict[str, SectionExplanation],
    plate_glossary: list[GlossaryItem],
) -> Plate:
    plate_sections: list[PlateSection] = []

    # build our place sections from our pages
    for page in pdf_pages:
        page_sections = filtered_sections_by_page_id[page.page_id]
        for page_section in page_sections.sections:
            if page_section.is_pruned:
                continue

            eli5 = explanations_by_section_id.get(page_section.section_id, None)

            plate_sections.append(
                PlateSection(
                    section_id=page_section.section_id,
                    section_type=page_section.section_type,
                    page_image_upath=page.image_upath,
                    explanation_id=eli5.explanation_id if eli5 else None,
                    part_ids=page_section.part_ids,
                )
            )

    # build our plate texts and images from our output texts and processed images
    texts = [PlateText(text_id=t.text_id, text=t.text) for t in plate_output_texts_by_id.values()]
    images = [PlateImage(image_id=i.image_id, upath=i.crop.upath, caption_id=i.image_id) for i in processed_images_by_id.values()]

    return Plate(
        title=pdf_title_config,
        language_code=plate_language_config,
        sections=plate_sections,
        images=images,
        texts=texts,
        glossary=plate_glossary,
    )


def plate_path(run_output_dir_config: str, generated_plate: Plate, custom_plate_path_config: str) -> str:
    plate_json = generated_plate.model_dump_json(indent=2)
    path = write_text_file(f"{run_output_dir_config}/plate.json", plate_json)
    return path if not custom_plate_path_config else custom_plate_path_config


@cache(behavior="recompute")
def plate_hash(plate_path: str) -> str:
    return calculate_file_hash(plate_path)


def plate(plate_path: str, plate_hash: str) -> Plate:
    with open(plate_path, "r", encoding="utf-8") as f:
        plate_data = json.load(f)
    return Plate.model_validate(plate_data)


def plate_texts(plate: Plate) -> list[PlateText]:
    return plate.texts


def plate_glossary(
    filtered_sections_by_page_id: dict[str, PageSections], section_glossaries_by_id: dict[str, SectionGlossary]
) -> list[GlossaryItem]:
    # build glossary from all section glossaries, we keep the first definition we see
    glossary_items = dict[str, GlossaryItem]()
    for page_sections in filtered_sections_by_page_id.values():
        for page_section in page_sections.sections:
            if page_section.is_pruned:
                continue

            for item in section_glossaries_by_id[page_section.section_id].items:
                if item.word not in glossary_items:
                    glossary_items[item.word] = item
    return list(sorted(glossary_items.values(), key=lambda x: x.word))


def plate_glossary_translations(
    glossary_translation_prompt_config: PromptConfig,
    plate_language_config: str,
    output_languages_config: list[str],
    plate_glossary: list[GlossaryItem],
) -> dict[str, list[GlossaryItem]]:
    glossary_translations: dict[str, list[GlossaryItem]] = {}

    def translate_glossary_to_lang(output_language: str):
        async def translate_glossary():
            tasks = []
            for item in plate_glossary:
                tasks.append(
                    get_glossary_translation(
                        glossary_translation_prompt_config,
                        plate_language_config,
                        output_language,
                        item,
                    )
                )

            return await gather_with_limit(tasks, glossary_translation_prompt_config.rate_limit)

        return translate_glossary

    for language in output_languages_config:
        if language == plate_language_config:
            glossary_translations[language] = plate_glossary
            continue

        glossary_translations[language] = sorted(run_async_task(translate_glossary_to_lang(language)), key=lambda x: x.word)

    return glossary_translations


def plate_output_texts_by_id(
    text_translation_prompt_config: PromptConfig,
    filtered_pdf_texts: dict[str, PageTexts],
    easy_reads_by_text_id: dict[str, EasyReadText],
    image_captions_by_id: dict[str, ImageCaption],
    explanations_by_section_id: dict[str, SectionExplanation],
    input_language_config: str,
    plate_language_config: str,
) -> dict[str, OutputText]:
    texts_by_id = {}

    # noop if input and output languages are the same
    if input_language_config == plate_language_config:
        for page_texts in filtered_pdf_texts.values():
            for text in page_texts.texts:
                texts_by_id[text.text_id] = OutputText(
                    text_id=text.text_id,
                    text=text.text,
                    language_code=plate_language_config,
                    reasoning="",
                )
                easy_read = easy_reads_by_text_id[text.text_id]
                texts_by_id[easy_read.easy_read_id] = OutputText(
                    text_id=easy_read.easy_read_id,
                    text=easy_read.easy_read,
                    language_code=plate_language_config,
                    reasoning="",
                )
        for key, caption in image_captions_by_id.items():
            texts_by_id[key] = OutputText(
                text_id=key,
                text=caption.caption,
                language_code=plate_language_config,
                reasoning="",
            )

        for explanation in explanations_by_section_id.values():
            texts_by_id[explanation.explanation_id] = OutputText(
                text_id=explanation.explanation_id,
                text=explanation.explanation,
                language_code=plate_language_config,
                reasoning="",
            )

        return texts_by_id

    async def translate_texts():
        tasks = []
        for page_texts in filtered_pdf_texts.values():
            for text in page_texts.texts:
                tasks.append(
                    get_text_translation(
                        text_translation_prompt_config,
                        text.text_id,
                        text.text,
                        input_language_config,
                        plate_language_config,
                    )
                )
                tasks.append(
                    get_text_translation(
                        text_translation_prompt_config,
                        easy_reads_by_text_id[text.text_id].easy_read_id,
                        easy_reads_by_text_id[text.text_id].easy_read,
                        input_language_config,
                        plate_language_config,
                    )
                )

        for key, caption in image_captions_by_id.items():
            tasks.append(
                get_text_translation(
                    text_translation_prompt_config,
                    key,
                    caption.text,
                    input_language_config,
                    plate_language_config,
                )
            )

        for explanation in explanations_by_section_id.values():
            tasks.append(
                get_text_translation(
                    text_translation_prompt_config,
                    explanation.explanation_id,
                    explanation.explanation,
                    input_language_config,
                    plate_language_config,
                )
            )

        return await gather_with_limit(tasks, text_translation_prompt_config.rate_limit)

    texts = run_async_task(translate_texts)
    for t in texts:
        texts_by_id[t.text_id] = t
    return texts_by_id


def plate_translations(
    text_translation_prompt_config: PromptConfig,
    plate_language_config: str,
    plate_texts: list[PlateText],
    output_languages_config: list[str],
) -> dict[str, dict[str, str]]:
    plate_translations: dict[str, dict[str, str]] = {}

    async def translate_texts():
        tasks = []
        for output_language in output_languages_config:
            if output_language == plate_language_config:
                plate_translations[output_language] = {t.text_id: t.text for t in plate_texts}
                continue

            plate_translations[output_language] = {}
            for text in plate_texts:
                tasks.append(
                    get_text_translation(
                        text_translation_prompt_config,
                        text.text_id,
                        text.text,
                        plate_language_config,
                        output_language,
                    )
                )

        return await gather_with_limit(tasks, text_translation_prompt_config.rate_limit)

    texts = run_async_task(translate_texts)
    for text in texts:
        plate_translations[text.language_code][text.text_id] = text.text

    return plate_translations
