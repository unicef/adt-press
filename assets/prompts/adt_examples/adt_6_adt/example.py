from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

ADT_6_ADT_EXAMPLE: list[messages.Example] = [
    messages.Example(
        debug_name="adt_6_adt_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/adt_6_adt/6_adt.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.table_of_contents,
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-6-0",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="Índice",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-6-1",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Yo soy Yacaré",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-6-3",
                    type=datatypes.ExtractedTextType.section_text,
                    text="A ciencia cierta. La explicación",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-6-4",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Los biomas",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-6-6",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Función de los bosques",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-6-8",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Cuestión de puntos de vista. La argumentación",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-6-9",
                    type=datatypes.ExtractedTextType.section_text,
                    text="«Antiprincesas» latinoamericanas rompen los estereotipos de los cuentos de hadas",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-6-11",
                    type=datatypes.ExtractedTextType.section_text,
                    text="La igualdad de género también es problema de ustedes",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-6-13",
                    type=datatypes.ExtractedTextType.section_text,
                    text="A puro cuento. La narración",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-6-14",
                    type=datatypes.ExtractedTextType.section_text,
                    text="La taberna del loro en el hombro",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-6-16",
                    type=datatypes.ExtractedTextType.section_text,
                    text="La catástrofe del acorazado brasileño Solimoes",
                )
            ),
        ],
    ),
    messages.Example(
        debug_name="adt_6_adt_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/adt_6_adt/6_adt.html",
            ),
        ],
    ),
]

if __name__ == "__main__":
    print([m.to_message_format() for m in ADT_6_ADT_EXAMPLE])
