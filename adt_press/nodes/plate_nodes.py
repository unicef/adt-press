import json

from hamilton.function_modifiers import cache

from adt_press.data.image import ProcessedImage
from adt_press.data.pdf import Page
from adt_press.data.plate import Plate, PlateImage, PlateSection, PlateText
from adt_press.data.section import PageSections, SectionEasyRead, SectionExplanation, SectionGlossary
from adt_press.data.text import OutputText
from adt_press.llm.prompt import PromptConfig
from adt_press.llm.text_translation import get_text_translation
from adt_press.utils.file import calculate_file_hash, write_text_file
from adt_press.utils.sync import gather_with_limit, run_async_task


def generated_plate(
    pdf_title_config: str,
    plate_language_config: str,
    pdf_pages: list[Page],
    filtered_sections_by_page_id: dict[str, PageSections],
    processed_images_by_id: dict[str, ProcessedImage],
    output_pdf_texts_by_id: dict[str, OutputText],
    explanations_by_section_id: dict[str, SectionExplanation],
    section_glossaries_by_id: dict[str, SectionGlossary],
    section_easy_reads_by_id: dict[str, SectionEasyRead],
) -> Plate:
    images: dict[str, PlateImage] = {}
    texts: dict[str, PlateText] = {}
    plate_sections: list[PlateSection] = []

    for page in pdf_pages:
        page_sections = filtered_sections_by_page_id[page.page_id]
        for page_section in page_sections.sections:
            if page_section.is_pruned:
                continue

            plate_sections.append(
                PlateSection(
                    section_id=page_section.section_id,
                    section_type=page_section.section_type,
                    page_image_upath=page.image_upath,
                    explanation=explanations_by_section_id[page_section.section_id].explanation,
                    easy_read=section_easy_reads_by_id[page_section.section_id].text,
                    glossary=section_glossaries_by_id[page_section.section_id].items,
                    part_ids=page_section.part_ids,
                )
            )

            for part_id in page_section.part_ids:
                if part_id in processed_images_by_id:
                    img = processed_images_by_id[part_id]
                    images[img.image_id] = PlateImage(image_id=img.image_id, upath=img.crop.upath, caption=img.caption.caption)
                else:
                    txt = output_pdf_texts_by_id[part_id]
                    texts[txt.text_id] = PlateText(text_id=txt.text_id, text=txt.text)

    return Plate(
        title=pdf_title_config,
        language_code=plate_language_config,
        sections=plate_sections,
        images=images.values(),
        texts=texts.values(),
    )


def plate_path(output_dir_config: str, generated_plate: Plate) -> str:
    plate_json = generated_plate.model_dump_json(indent=2)
    return write_text_file(f"{output_dir_config}/plate.json", plate_json)


@cache(behavior="recompute")
def plate_hash(plate_path: str) -> str:
    return calculate_file_hash(plate_path)


def plate(plate_path: str, plate_hash: str) -> Plate:
    with open(plate_path, "r", encoding="utf-8") as f:
        plate_data = json.load(f)
    return Plate.model_validate(plate_data)


def plate_texts(plate: Plate) -> list[PlateText]:
    return plate.texts


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
