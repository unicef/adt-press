import os

from hamilton.function_modifiers import cache

from adt_press.models.config import TemplateConfig
from adt_press.models.epub import create_epub_file
from adt_press.models.plate import Plate
from adt_press.models.web import WebPage


@cache(behavior="recompute")
def package_epub(
    template_config: TemplateConfig,
    run_output_dir_config: str,
    pdf_title_config: str,
    plate_language_config: str,
    plate: Plate,
    plate_translations: dict[str, dict[str, str]],
    web_pages: list[WebPage],
    package_adt_web: str,  # Dependency to ensure web packaging runs first
) -> dict[str, str]:
    """
    Generate EPUB files for each language translation.

    Returns:
        Dictionary mapping language codes to EPUB file paths
    """
    epub_paths = {}
    adt_dir = os.path.join(run_output_dir_config, "adt")
    image_dir = os.path.join(adt_dir, "images")

    plate_texts = {txt.text_id: txt for txt in plate.texts}

    # Load CSS if available
    css_content = None
    css_path = os.path.join(adt_dir, "assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            css_content = f.read()

    for language, translations in plate_translations.items():
        epub_filename = f"{pdf_title_config}_{language}.epub"
        epub_path = os.path.join(run_output_dir_config, epub_filename)

        create_epub_file(
            output_path=epub_path,
            title=plate.title,
            language=language,
            authors=plate.authors,
            plate=plate,
            web_pages=web_pages,
            plate_texts=plate_texts,
            translations=translations,
            image_dir=image_dir,
            css_content=css_content,
        )

        epub_paths[language] = epub_filename

    return epub_paths
