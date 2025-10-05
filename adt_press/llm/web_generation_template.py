# mypy: ignore-errors

from adt_press.models.config import TemplateRenderConfig
from adt_press.models.plate import PlateImage, PlateSection, PlateText
from adt_press.models.web import RenderTextGroup, WebPage
from adt_press.utils.html import render_template_to_string
from adt_press.utils.languages import LANGUAGE_MAP


async def generate_web_page_template(
    render_strategy: str,
    config: TemplateRenderConfig,
    section: PlateSection,
    groups: list[RenderTextGroup],
    texts: list[PlateText],
    images: list[PlateImage],
    language_code: str,
) -> WebPage:
    language = LANGUAGE_MAP[language_code]

    content = render_template_to_string(
        config.render_template_path,
        {
            "section": section,
            "language": language,
            "groups": {g.group_id: g.model_dump() for g in groups},
            "texts": {t.text_id: t.model_dump() for t in texts},
            "images": {i.image_id: i for i in images},
        },
    )

    return WebPage(
        text_id=texts[0].text_id if texts else "",
        section_id=section.section_id,
        reasoning="no reasoning, template based",
        content=content,
        image_ids=[i.image_id for i in images],
        text_ids=[t.text_id for t in texts],
        render_strategy=render_strategy,
    )
