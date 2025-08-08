"""
This is the front cover that is a different style to the rest of the ADT. It includes an interface for setting preferences before you start.
"""

from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

LIVINGURUGUAY1_ADT_FRONT_COVER_2: list[messages.Example] = [
    # Front Cover 2 - LivingUruguay1_0
    messages.Example(
        debug_name="front_cover_2_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/front_cover_2/livinguruguay1_0.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.text_and_images,
                )
            ),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-0-0")),
            messages.ImageContent(image_path="adt_examples/front_cover_2/images/img-0-0.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-0-1")),
            messages.ImageContent(image_path="adt_examples/front_cover_2/images/logo_anep.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-0-2")),
            messages.ImageContent(image_path="adt_examples/front_cover_2/images/logo_ceibal.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-0-3")),
            messages.ImageContent(image_path="adt_examples/front_cover_2/images/logo_consejo_secundaria.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-0-4")),
            messages.ImageContent(image_path="adt_examples/front_cover_2/images/logo_consejo_tecnico.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-0-5")),
            messages.ImageContent(image_path="adt_examples/front_cover_2/images/logo_unicef.png"),
            messages.TextContent(text=adt_message_constants.TEXT_CONTEXT),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-0-0",
                    type=datatypes.ExtractedTextType.book_title,
                    text="#Living Uruguay1",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-0-1",
                    type=datatypes.ExtractedTextType.book_subtitle,
                    text="1st Grade English Book",
                )
            ),
        ],
    ),
    messages.Example(
        debug_name="front_cover_2_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/front_cover_2/livinguruguay1_0.html",
            ),
        ],
    ),
]

if __name__ == "__main__":
    # Just for debugging.
    print([m.to_message_format() for m in LIVINGURUGUAY1_ADT_FRONT_COVER_2])
