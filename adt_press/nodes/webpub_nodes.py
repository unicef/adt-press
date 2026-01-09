import os
import shutil
from datetime import datetime

import structlog
from hamilton.function_modifiers import cache

from adt_press.models.config import TemplateConfig
from adt_press.models.plate import Plate
from adt_press.models.web import WebPage
from adt_press.utils.file import write_json_file
from adt_press.utils.web_assets import build_config_json

log = structlog.get_logger(__name__)


@cache(behavior="recompute")
def package_webpub(
    template_config: TemplateConfig,
    pdf_title_config: str,
    run_output_dir_config: str,
    plate: Plate,
    plate_translations: dict[str, dict[str, str]],
    web_pages: list[WebPage],
    strategy_config: dict[str, str],
    package_adt_web: str,
) -> str:
    languages = list(plate_translations.keys())
    default_language = languages[0]

    reading_order: list[dict[str, str]] = []
    resources: list[dict[str, str]] = []

    metadata: dict[str, str] = {
        "@type": "http://schema.org/Book",
        "title": plate.title,
        "language": default_language,
        "modified": datetime.now().isoformat(),
    }

    if plate.authors:
        metadata["author"] = ", ".join(plate.authors)

    if plate.publisher:
        metadata["publisher"] = plate.publisher

    adt_dir = os.path.join(run_output_dir_config, "adt")

    links: list[dict[str, str]] = [
        {
            "rel": "self",
            "href": "manifest.json",
            "type": "application/webpub+json",
        },
    ]

    if plate.cover_image_id:
        cover_href = None
        cover_type = "image/png"
        for filename, mime_type in (
            ("cover.png", "image/png"),
            ("cover.jpg", "image/jpeg"),
            ("cover.jpeg", "image/jpeg"),
        ):
            if os.path.exists(os.path.join(adt_dir, filename)):
                cover_href = filename
                cover_type = mime_type
                break

        if cover_href:
            links.append(
                {
                    "rel": "cover",
                    "href": cover_href,
                    "type": cover_type,
                }
            )

    manifest = {
        "@context": "https://readium.org/webpub-manifest/context.jsonld",
        "metadata": metadata,
        "links": links,
        "readingOrder": reading_order,
        "resources": resources,
    }

    sections_by_id = {section.section_id: section for section in plate.sections}
    quizzes_by_id = {quiz.quiz_id: quiz for quiz in plate.quizzes}

    def section_number_for_page(webpage: WebPage) -> int:
        section = sections_by_id.get(webpage.section_id)
        if section and section.page_number is not None:
            return section.page_number
        quiz = quizzes_by_id.get(webpage.section_id)
        if quiz:
            parent_section = sections_by_id.get(quiz.section_id)
            if parent_section and parent_section.page_number is not None:
                return parent_section.page_number
        log.warning("webpage references unknown section; defaulting page number", section_id=webpage.section_id)
        return 0

    # populate our reading order from our web pages
    for webpage in web_pages:
        page_number = section_number_for_page(webpage)
        title = f"{page_number}"
        if len(webpage.text_ids):
            title += f" - {plate_translations[default_language].get(webpage.text_ids[0], '')}"

        page_entry = {
            "href": f"{webpage.section_id}.html",
            "type": "text/html",
            "title": title,
        }
        reading_order.append(page_entry)

    webpub_dir = os.path.join(run_output_dir_config, "webpub")
    if os.path.exists(webpub_dir):
        shutil.rmtree(webpub_dir)  # pragma: no cover

    # copy all our assets over from our built adt directory
    shutil.copytree(adt_dir, webpub_dir)

    build_config_json(
        template_config,
        run_output_dir_config,
        book_title=pdf_title_config,
        languages=languages,
        default_language=default_language,
        strategy_config=strategy_config,
        output_subdir="webpub",
        feature_overrides={
            "showNavigationControls": False,
            "showTutorial": False,
        },
    )

    # now add all our resources to the manifest
    for root, dirs, files in os.walk(webpub_dir):
        for file in files:
            file_path = os.path.relpath(os.path.join(root, file), webpub_dir)
            mime_type = "application/octet-stream"
            if file.endswith(".html"):
                mime_type = "text/html"
            elif file.endswith(".css"):
                mime_type = "text/css"
            elif file.endswith(".png"):
                mime_type = "image/png"
            elif file.endswith(".jpg") or file.endswith(".jpeg"):
                mime_type = "image/jpeg"
            elif file.endswith(".mp3"):
                mime_type = "audio/mpeg"
            elif file.endswith(".js"):
                mime_type = "application/javascript"
            elif file.endswith(".json"):
                mime_type = "application/json"

            resource_entry = {
                "href": file_path.replace("\\", "/"),
                "type": mime_type,
            }

            resources.append(resource_entry)

    # write out the manifest file
    manifest_path = os.path.join(webpub_dir, "manifest.json")
    write_json_file(manifest_path, manifest)

    # zip it into a standalone webpub file
    webpub_filename = f"{pdf_title_config}.webpub"
    webpub_path = os.path.join(run_output_dir_config, webpub_filename)
    shutil.make_archive(
        base_name=webpub_path.replace(".webpub", ""),
        format="zip",
        root_dir=webpub_dir,
    )
    # rename .zip to .webpub
    os.rename(webpub_path.replace(".webpub", ".zip"), webpub_path)

    return "done"
