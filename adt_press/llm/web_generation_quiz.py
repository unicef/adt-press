# mypy: ignore-errors

from adt_press.models.config import TemplateRenderConfig
from adt_press.models.plate import PlateImage, PlateQuiz, PlateSection, PlateText
from adt_press.models.web import RenderTextGroup, WebPage
from adt_press.utils.html import render_template_to_string
from adt_press.utils.languages import LANGUAGE_MAP


async def generate_web_quiz(
    render_strategy: str,
    config: TemplateRenderConfig,
    language_code: str,
    quiz: PlateQuiz,
    texts: list[PlateText],
) -> WebPage:
    language = LANGUAGE_MAP[language_code]

    content = render_template_to_string(
        config.render_template_path,
        {
            "quiz": quiz,
            "language": language,
            "texts": {t.text_id: t.model_dump() for t in texts},
        },
    )

    return WebPage(
        text_id=texts[0].text_id if texts else "",
        section_id=quiz.quiz_id,
        reasoning="no reasoning, template based",
        content=content,
        image_ids=[],
        text_ids=[t.text_id for t in texts],
        render_strategy=render_strategy,
    )
