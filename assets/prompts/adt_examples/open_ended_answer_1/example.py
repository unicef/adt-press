from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

CUADERNO3_ADT_ACTIVITY_OPEN_ENDED_ANSWER_1: list[messages.Example] = [
    # open_ended_answer_1 - cuaderno3_17_section_0
    messages.Example(
        debug_name="open_ended_answer_1_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/open_ended_answer_1/cuaderno3_17.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.activity_open_ended_answer,
                )
            ),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-17-0")),
            messages.ImageContent(image_path="adt_examples/open_ended_answer_1/images/c3_17_0.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-0",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="Esta es Elena.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-1",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Completa los cuadros vacíos agregando información sobre ella.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-2",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Melena despeinada por correr.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-3",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Corazón que late rápido cuando corre.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-4",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Piernas muy veloces.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-5",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Rodillas lastimadas.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-6",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Championes.",
                )
            ),
        ],
    ),
    messages.Example(
        debug_name="open_ended_answer_1_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/open_ended_answer_1/cuaderno3_17_section_0.html",
            )
        ],
    ),
]

if __name__ == "__main__":
    # Just for debugging.
    print([m.to_message_format() for m in CUADERNO3_ADT_ACTIVITY_OPEN_ENDED_ANSWER_1])
