from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

ADT_16_0_ADT_EXAMPLE: list[messages.Example] = [
    messages.Example(
        debug_name="adt_16_0_adt_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/adt_16_0_adt/16_0_adt.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.activity_fill_in_the_blank,
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-16-0",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="¿Cuál es el tema?",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-16-1",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Observa los encabezados y las partes del texto que acabas de leer de 'Los Biomas' en la página 12.1",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-16-20",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Ver todo el texto de Los Biomas en una sola página.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-16-2",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Completa este esquema llenando los encabezados del texto de la lectura.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-16-3",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Título principal",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-16-4",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Primer subtítulo",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-16-5",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Segundo subtítulo",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-16-6",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Primer subtítulo",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-16-8",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Segundo subtítulo",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-16-9",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Tercer subtítulo",
                )
            ),
        ],
    ),
    messages.Example(
        debug_name="adt_16_0_adt_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/adt_16_0_adt/16_0_adt.html",
            ),
        ],
    ),
]

if __name__ == "__main__":
    print([m.to_message_format() for m in ADT_16_0_ADT_EXAMPLE])
