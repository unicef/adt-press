from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

CUADERNO3_ADT_ACTIVITY_FILL_IN_THE_BLANK_1: list[messages.Example] = [
    messages.Example(
        debug_name="activity_fill_in_the_blank_1_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/activity_fill_in_the_blank_1/cuaderno3_25.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.activity_fill_in_the_blank,
                )
            ),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-25-0")),
            messages.ImageContent(image_path="adt_examples/activity_fill_in_the_blank_1/images/c3_25_0.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-0",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="Actividad 14",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-1",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Escribe en la línea punteada el pronombre que corresponde.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-2",
                    type=datatypes.ExtractedTextType.section_text,
                    text="A Elena le encantaba correr carreras.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-3",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Corría contra ",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-4",
                    type=datatypes.ExtractedTextType.section_text,
                    text=" hermano que gateaba.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-5",
                    type=datatypes.ExtractedTextType.section_text,
                    text="—¡¡Gané!!",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-6",
                    type=datatypes.ExtractedTextType.section_text,
                    text="También corría contra ",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-7",
                    type=datatypes.ExtractedTextType.section_text,
                    text=" perro.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-8",
                    type=datatypes.ExtractedTextType.section_text,
                    text="—¡¡Perdí!!",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-9",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Desafiaba a ",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-10",
                    type=datatypes.ExtractedTextType.section_text,
                    text=" tortuga.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-11",
                    type=datatypes.ExtractedTextType.section_text,
                    text="—¡¡Gané!!",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-12",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Y no tenía miedo de correr contra ",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-13",
                    type=datatypes.ExtractedTextType.section_text,
                    text=" papá.",
                )
            ),
        ],
    ),
    messages.Example(
        debug_name="activity_fill_in_the_blank_1_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[messages.AssistantHTMLADTContent(html_path="adt_examples/activity_fill_in_the_blank_1/cuaderno3_25_section_0.html")],
    ),
]

if __name__ == "__main__":
    # Just for debugging.
    print([m.to_message_format() for m in CUADERNO3_ADT_ACTIVITY_FILL_IN_THE_BLANK_1])
