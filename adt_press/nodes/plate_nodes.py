import json

from hamilton.function_modifiers import cache

from adt_press.llm.glossary_translation import get_glossary_translation
from adt_press.llm.text_translation import get_text_translation
from adt_press.models.config import PromptConfig
from adt_press.models.image import ImageCaption, ProcessedImage
from adt_press.models.pdf import Page
from adt_press.models.plate import Plate, PlateGroup, PlateImage, PlateSection, PlateText
from adt_press.models.section import GlossaryItem, PageSections, SectionExplanation, SectionGlossary, SectionMetadata
from adt_press.models.text import EasyReadText, OutputText, PageTexts
from adt_press.utils.file import calculate_file_hash, write_text_file
from adt_press.utils.sync import gather_with_limit, run_async_task


def generated_plate(
    pdf_title_config: str,
    plate_language_config: str,
    pdf_pages: list[Page],
    filtered_sections_by_page_id: dict[str, PageSections],
    processed_images_by_id: dict[str, ProcessedImage],
    plate_groups: list[PlateGroup],
    plate_output_texts_by_id: dict[str, OutputText],
    explanations_by_section_id: dict[str, SectionExplanation],
    section_metadata_by_id: dict[str, SectionMetadata],
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

            metadata = section_metadata_by_id[page_section.section_id]

            plate_sections.append(
                PlateSection(
                    section_id=page_section.section_id,
                    section_type=page_section.section_type,
                    page_image_path=page.page_image_path,
                    explanation_id=eli5.explanation_id if eli5 else None,
                    part_ids=page_section.part_ids,
                    layout_type=metadata.layout_type,
                    background_color=metadata.background_color,
                    text_color=metadata.text_color,
                )
            )

    # build our plate texts and images from our output texts and processed images
    texts = [PlateText(text_id=t.text_id, text=t.text) for t in plate_output_texts_by_id.values()]
    images = [PlateImage(image_id=i.image_id, image_path=i.crop.image_path, caption_id=i.image_id) for i in processed_images_by_id.values()]
    

    return Plate(
        title=pdf_title_config,
        language_code=plate_language_config,
        sections=plate_sections,
        images=images,
        groups=plate_groups,
        texts=texts,
        glossary=plate_glossary if plate_glossary else [],
    )


def plate_sections_by_id(plate: Plate) -> dict[str, PlateSection]:
    return {section.section_id: section for section in plate.sections}


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
    glossary_items: dict[str, GlossaryItem] = {}
    for page_sections in filtered_sections_by_page_id.values():
        for page_section in page_sections.sections:
            if page_section.is_pruned:
                continue

            section_glossary = section_glossaries_by_id.get(page_section.section_id, None)
            if section_glossary:
                for item in section_glossary.items:
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


def plate_groups(filtered_pdf_texts: dict[str, PageTexts]) -> list[PlateGroup]:
    groups = []
    for page_texts in filtered_pdf_texts.values():
        for g in page_texts.groups:
            groups.append(PlateGroup(group_id=g.group_id, group_type=g.group_type, text_ids=[t.text_id for t in g.texts]))
    return groups


def plate_output_texts_by_id(
    text_translation_prompt_config: PromptConfig,
    filtered_pdf_texts: dict[str, PageTexts],
    easy_reads_by_text_id: dict[str, EasyReadText],
    image_captions_by_id: dict[str, ImageCaption],
    explanations_by_section_id: dict[str, SectionExplanation],
    input_language_config: str,
    plate_language_config: str,
) -> dict[str, OutputText]:
    # Collect all texts that need processing
    texts_to_process = []

    # Page texts and easy reads
    for page_texts in filtered_pdf_texts.values():
        for page_group in page_texts.groups:
            for text in page_group.texts:
                texts_to_process.append((text.text_id, text.text))

                easy_read = easy_reads_by_text_id.get(text.text_id, None)
                if easy_read:
                    texts_to_process.append((easy_read.easy_read_id, easy_read.easy_read))

    # Image captions
    for key, caption in image_captions_by_id.items():
        if caption.caption:
            texts_to_process.append((key, caption.caption))

    # Explanations
    for explanation in explanations_by_section_id.values():
        texts_to_process.append((explanation.explanation_id, explanation.explanation))

    # Handle same language case (no translation needed)
    if input_language_config == plate_language_config:
        return {
            text_id: OutputText(
                text_id=text_id,
                text=text_content,
                language_code=plate_language_config,
                reasoning="",
            )
            for text_id, text_content in texts_to_process
        }

    # Handle translation case
    async def translate_texts():
        tasks = [
            get_text_translation(
                text_translation_prompt_config,
                text_id,
                text_content,
                input_language_config,
                plate_language_config,
            )
            for text_id, text_content in texts_to_process
        ]
        return await gather_with_limit(tasks, text_translation_prompt_config.rate_limit)

    texts = run_async_task(translate_texts)
    return {t.text_id: t for t in texts}


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
