import os

from hamilton.function_modifiers import cache

from adt_press.models.config import TemplateConfig
from adt_press.models.epub import create_epub_file
from adt_press.models.plate import Plate
from adt_press.models.web import WebPage
from adt_press.utils.web_assets import build_config_json


@cache(behavior="recompute")
def package_epub(
    template_config: TemplateConfig,
    run_output_dir_config: str,
    pdf_title_config: str,
    plate_language_config: str,
    plate: Plate,  # This is the issue - plate object has wrong paths
    plate_translations: dict[str, dict[str, str]],
    web_pages: list[WebPage],
    strategy_config: dict[str, str],
    package_adt_web: str,
) -> dict[str, str]:
    """
    Generate EPUB files for each language translation.

    Returns:
        Dictionary mapping language codes to EPUB file paths
    """
    epub_paths = {}
    adt_dir = os.path.join(run_output_dir_config, "adt")

    languages = list(plate_translations.keys())
    default_language = languages[0]
    feature_overrides = {
        "showNavigationControls": False,
        "showTutorial": False,
    }

    build_config_json(
        template_config,
        run_output_dir_config,
        book_title=pdf_title_config,
        languages=languages,
        default_language=default_language,
        strategy_config=strategy_config,
        output_subdir="epub",
        feature_overrides=feature_overrides,
    )

    plate_texts = {txt.text_id: txt for txt in plate.texts}

    # Load CSS if available
    css_content = None
    css_path = os.path.join(adt_dir, "assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
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
            image_dir=os.path.join(run_output_dir_config, "images"),  # Fixed: correct image directory
            css_content=css_content,
        )

        epub_paths[language] = epub_filename

    return epub_paths
