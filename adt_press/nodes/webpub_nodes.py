import json
import os
import shutil
from datetime import datetime

from hamilton.function_modifiers import cache

from adt_press.models.config import TemplateConfig
from adt_press.models.plate import Plate
from adt_press.models.section import GlossaryItem
from adt_press.models.speech import SpeechFile
from adt_press.models.web import WebPage
from adt_press.utils.web_assets import build_config_json


@cache(behavior="recompute")
def package_webpub(
    template_config: TemplateConfig,
    pdf_title_config: str,
    run_output_dir_config: str,
    plate_language_config: str,
    plate: Plate,
    plate_translations: dict[str, dict[str, str]],
    plate_glossary_translations: dict[str, list[GlossaryItem]],
    speech_files: dict[str, dict[str, SpeechFile]],
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

    links: list[dict[str, str]] = [
        {
            "rel": "self",
            "href": "manifest.json",
            "type": "application/webpub+json",
        },
    ]

    if plate.cover_image_id:
        links.append(
            {
                "rel": "cover",
                "href": "cover.png",
                "type": "image/png",
            }
        )

    manifest = {
        "@context": "https://readium.org/webpub-manifest/context.jsonld",
        "metadata": metadata,
        "links": links,
        "readingOrder": reading_order,
        "resources": resources,
    }

    # populate our reading order from our web pages
    for webpage in web_pages:
        page_entry = {
            "href": f"{webpage.section_id}.html",
            "type": "text/html",
        }
        reading_order.append(page_entry)

    webpub_dir = os.path.join(run_output_dir_config, "webpub")
    if os.path.exists(webpub_dir):
        shutil.rmtree(webpub_dir)  # pragma: no cover

    # copy all our assets over from our built adt directory
    adt_dir = os.path.join(run_output_dir_config, "adt")
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
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=4)

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
