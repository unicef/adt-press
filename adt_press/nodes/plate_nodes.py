import json

from hamilton.function_modifiers import cache

from adt_press.llm.glossary_translation import get_glossary_translation
from adt_press.llm.text_translation import get_text_translation
from adt_press.models.config import PromptConfig, TextTypeName
from adt_press.models.ids import ImageID, PageID, SectionID, TextID
from adt_press.models.image import ImageCaption, ProcessedImage
from adt_press.models.metadata import BookChapter, BookMetadata
from adt_press.models.pdf import Page
from adt_press.models.plate import Plate, PlateChapter, PlateGroup, PlateImage, PlateQuiz, PlateSection, PlateText
from adt_press.models.quiz import SectionQuiz
from adt_press.models.section import GlossaryItem, PageSections, SectionExplanation, SectionGlossary
from adt_press.models.text import EasyReadText, OutputText, PageTextGroups
from adt_press.utils.file import calculate_file_hash, write_text_file
from adt_press.utils.languages import Language, LanguageCode
from adt_press.utils.sync import gather_with_limit, run_async_task


def generated_plate(
    pdf_title_config: str,
    plate_language: Language,
    book_metadata: BookMetadata,
    pdf_pages: list[Page],
    filtered_sections_by_page_id: dict[PageID, PageSections],
    processed_images_by_id: dict[ImageID, ProcessedImage],
    plate_groups: list[PlateGroup],
    plate_output_texts_by_id: dict[TextID, OutputText],
    explanations_by_section_id: dict[SectionID, SectionExplanation],
    quizzes_by_section_id: dict[SectionID, SectionQuiz],
    plate_glossary: list[GlossaryItem],
) -> Plate:
    plate_sections: list[PlateSection] = []

    # build our place sections from our pages
    cover_image_path = None
    for page in pdf_pages:
        if page.page_id == book_metadata.cover_page_id:
            cover_image_path = page.page_image_path

        page_sections = filtered_sections_by_page_id[page.page_id]
        for page_section in page_sections.sections:
            if page_section.is_pruned:
                continue

            eli5 = explanations_by_section_id.get(page_section.section_id, None)

            plate_sections.append(
                PlateSection(
                    section_id=page_section.section_id,
                    section_type=page_section.section_type.name,
                    page_number=page_section.page_number,
                    page_image_path=page.page_image_path,
                    explanation_id=eli5.explanation_id if eli5 else None,
                    part_ids=page_section.part_ids,
                    background_color=page_section.background_color,
                    text_color=page_section.text_color,
                )
            )

    # build our quizzes
    quizzes: list[PlateQuiz] = []
    for quiz in quizzes_by_section_id.values():
        quizzes.append(
            PlateQuiz(
                quiz_id=quiz.quiz_id,
                section_id=quiz.section_id,
                question_id=quiz.question_id,
                option_ids=list(quiz.option_ids),
                explanation_ids=list(quiz.explanation_ids),
                answer_index=quiz.answer_index,
            )
        )

    # build our plate texts and images from our output texts and processed images
    texts = [PlateText(text_id=t.text_id, text_type=t.text_type, text=t.text) for t in plate_output_texts_by_id.values()]
    images = [
        PlateImage(image_id=ImageID(i.image_id), image_path=i.crop.image_path, caption_id=TextID(i.image_id))
        for i in processed_images_by_id.values()
    ]

    cover_image_id: ImageID | None = None
    if cover_image_path:
        cover_image_id = ImageID("cover")
        images.append(PlateImage(image_id=ImageID(cover_image_id), image_path=cover_image_path, caption_id=TextID(cover_image_id)))

    table_of_contents: list[PlateChapter] = []
    for chapter in book_metadata.table_of_contents:
        # find the first section id that matches this chapter's page number
        matching_section = next((sec for sec in plate_sections if sec.page_number == chapter.page_number), None)
        if matching_section:
            table_of_contents.append(PlateChapter(chapter_id=chapter.chapter_id, section_id=matching_section.section_id))

    return Plate(
        title=book_metadata.title or pdf_title_config,
        authors=book_metadata.authors,
        publisher=book_metadata.publisher,
        table_of_contents=table_of_contents,
        cover_image_id=cover_image_id,
        language_code=plate_language.code,
        sections=plate_sections,
        images=images,
        groups=plate_groups,
        texts=texts,
        quizzes=quizzes,
        glossary=plate_glossary if plate_glossary else [],
    )


def plate_sections_by_id(plate: Plate) -> dict[SectionID, PlateSection]:
    return {SectionID(section.section_id): section for section in plate.sections}


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
    filtered_sections_by_page_id: dict[PageID, PageSections], section_glossaries_by_id: dict[SectionID, SectionGlossary]
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
    plate_language: Language,
    output_languages: list[Language],
    plate_glossary: list[GlossaryItem],
) -> dict[LanguageCode, list[GlossaryItem]]:
    glossary_translations: dict[LanguageCode, list[GlossaryItem]] = {}

    def translate_glossary_to_lang(output_language: Language):
        async def translate_glossary():
            tasks = []
            for item in plate_glossary:
                tasks.append(
                    get_glossary_translation(
                        glossary_translation_prompt_config,
                        plate_language,
                        output_language,
                        item,
                    )
                )

            return await gather_with_limit(tasks, glossary_translation_prompt_config.rate_limit)

        return translate_glossary

    for language in output_languages:
        if language == plate_language:
            glossary_translations[language.code] = plate_glossary
            continue

        glossary_translations[language.code] = sorted(run_async_task(translate_glossary_to_lang(language)), key=lambda x: x.word)

    return glossary_translations


def plate_groups(processed_pdf_texts: dict[PageID, PageTextGroups]) -> list[PlateGroup]:
    groups = []
    for page_texts in processed_pdf_texts.values():
        for g in page_texts.groups:
            groups.append(PlateGroup(group_id=g.group_id, group_type=g.group_type, text_ids=[t.text_id for t in g.texts]))
    return groups


def plate_output_texts_by_id(
    text_translation_prompt_config: PromptConfig,
    processed_pdf_texts: dict[PageID, PageTextGroups],
    easy_reads_by_text_id: dict[TextID, EasyReadText],
    image_captions_by_id: dict[ImageID, ImageCaption],
    explanations_by_section_id: dict[SectionID, SectionExplanation],
    book_table_of_contents: list[BookChapter],
    quizzes_by_section_id: dict[SectionID, SectionQuiz],
    input_language: Language,
    plate_language: Language,
) -> dict[TextID, OutputText]:
    # Collect all texts that need processing
    texts_to_process: list[tuple[TextID, TextTypeName, str]] = []

    # Page texts and easy reads
    for page_texts in processed_pdf_texts.values():
        for page_group in page_texts.groups:
            for text in page_group.texts:
                texts_to_process.append((TextID(text.text_id), text.text_type, text.text))

                easy_read = easy_reads_by_text_id.get(text.text_id, None)
                if easy_read:
                    texts_to_process.append((TextID(easy_read.easy_read_id), text.text_type, easy_read.easy_read))

    # Image captions
    for key, caption in image_captions_by_id.items():
        if caption.caption:
            texts_to_process.append((TextID(key), TextTypeName("image_caption"), caption.caption))

    # Explanations
    for explanation in explanations_by_section_id.values():
        texts_to_process.append((TextID(explanation.explanation_id), TextTypeName("explanation"), explanation.explanation))

    # Chapter titles
    for chapter in book_table_of_contents:
        texts_to_process.append((TextID(chapter.chapter_id), TextTypeName("chapter_title"), chapter.title))

    # Quizzes
    for quiz in quizzes_by_section_id.values():
        texts_to_process.append((TextID(quiz.question_id), TextTypeName("quiz_question"), quiz.question))
        for idx, quiz_option in enumerate(quiz.options):
            texts_to_process.append((TextID(quiz.option_ids[idx]), TextTypeName("quiz_option"), quiz_option))
        for idx, quiz_explanation in enumerate(quiz.explanations):
            texts_to_process.append((TextID(quiz.explanation_ids[idx]), TextTypeName("quiz_explanation"), quiz_explanation))

    # Handle same language case (no translation needed)
    if input_language.code == plate_language.code:
        return {
            TextID(text_id): OutputText(
                text_id=text_id,
                text_type=text_type,
                text=text_content,
                language_code=plate_language.code,
                reasoning="",
            )
            for text_id, text_type, text_content in texts_to_process
        }

    # Handle translation case
    async def translate_texts():
        tasks = [
            get_text_translation(
                text_translation_prompt_config,
                [(text_id, text_type, text_content)],
                input_language,
                plate_language,
            )
            for text_id, text_type, text_content in texts_to_process
        ]
        return await gather_with_limit(tasks, text_translation_prompt_config.rate_limit)

    results = run_async_task(translate_texts)
    # Flatten results - each result is a list with one item
    texts = [text for result_list in results for text in result_list]
    return {TextID(t.text_id): t for t in texts}


def plate_translations(
    text_translation_prompt_config: PromptConfig,
    plate_language: Language,
    plate_groups: list[PlateGroup],
    plate_texts: list[PlateText],
    output_languages: list[Language],
) -> dict[LanguageCode, dict[TextID, str]]:
    plate_translations: dict[LanguageCode, dict[TextID, str]] = {}

    # Create a lookup for plate texts by ID
    plate_texts_by_id = {t.text_id: t for t in plate_texts}

    # Identify which text IDs are in groups
    text_ids_in_groups = set()
    for group in plate_groups:
        text_ids_in_groups.update(group.text_ids)

    # Identify texts not in any group
    ungrouped_text_ids = set(plate_texts_by_id.keys()) - text_ids_in_groups

    async def translate_texts():
        tasks = []
        for output_language in output_languages:
            if output_language == plate_language:
                plate_translations[output_language.code] = {t.text_id: t.text for t in plate_texts}
                continue

            plate_translations[output_language.code] = {}

            # Process each group together to maintain context
            for group in plate_groups:
                # Gather all texts in this group
                group_texts = []
                for text_id in group.text_ids:
                    if text_id in plate_texts_by_id:
                        text = plate_texts_by_id[text_id]
                        group_texts.append((text.text_id, text.text_type, text.text))

                # Skip empty groups
                if not group_texts:
                    continue

                # Translate the entire group at once
                tasks.append(
                    get_text_translation(
                        text_translation_prompt_config,
                        group_texts,
                        plate_language,
                        output_language,
                    )
                )

            # Process ungrouped texts individually (as single-item groups)
            for text_id in ungrouped_text_ids:
                text = plate_texts_by_id[text_id]
                tasks.append(
                    get_text_translation(
                        text_translation_prompt_config,
                        [(text.text_id, text.text_type, text.text)],
                        plate_language,
                        output_language,
                    )
                )

        return await gather_with_limit(tasks, text_translation_prompt_config.rate_limit)

    results = run_async_task(translate_texts)

    # Flatten the results - all results are now lists
    for result_list in results:
        for text in result_list:
            plate_translations[text.language_code][text.text_id] = text.text

    return plate_translations
