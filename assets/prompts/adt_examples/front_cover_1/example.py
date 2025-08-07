"""
This is the front cover that is a different style to the rest of the ADT. It includes an interface for setting preferences before you start.
"""

from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

CUADERNO3_ADT_FRONT_COVER_1: list[messages.Example] = [
    # Front Cover 1 - Cuaderno3_0
    messages.Example(
        debug_name="front_cover_1_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/front_cover_1/cuaderno3_0.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.text_and_images,
                )
            ),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-0-0")),
            messages.ImageContent(image_path="adt_examples/front_cover_1/images/img-0-0.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-0-1")),
            messages.ImageContent(image_path="adt_examples/front_cover_1/images/logo_anep.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-0-2")),
            messages.ImageContent(image_path="adt_examples/front_cover_1/images/logo_ceibal.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-0-3")),
            messages.ImageContent(image_path="adt_examples/front_cover_1/images/logo_unicef.png"),
            messages.TextContent(text=adt_message_constants.TEXT_CONTEXT),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-0-0",
                    type=datatypes.ExtractedTextType.book_title,
                    text="Cuaderno para leer y escribir",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-0-1",
                    type=datatypes.ExtractedTextType.book_title,
                    text="En tercero",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-0-2",
                    type=datatypes.ExtractedTextType.book_subtitle,
                    text="Educación Inicial y Primaria",
                )
            ),
        ],
    ),
    messages.Example(
        debug_name="front_cover_1_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/front_cover_1/cuaderno3_0.html",
            ),
        ],
    ),
]

if __name__ == "__main__":
    # Just for debugging.
    print([m.to_message_format() for m in CUADERNO3_ADT_FRONT_COVER_1])
