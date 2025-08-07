from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

ADT_19_1_ADT_EXAMPLE: list[messages.Example] = [
    messages.Example(
        debug_name="adt_19_1_adt_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/adt_19_1_adt/19_1_adt.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.activity_open_ended_answer,
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-19-0",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="Interrogantes",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-19-13",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text='Escribe tres preguntas que puedas contestar leyendo el apartado "Tipos de biomas".',
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-19-23",
                    type=datatypes.ExtractedTextType.boxed_text,
                    text="¿Te diste cuenta!? A veces, para encontrar una respuesta es necesario leer más de una vez.",
                )
            ),
        ],
    ),
    messages.Example(
        debug_name="adt_19_1_adt_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/adt_19_1_adt/19_1_adt.html",
            ),
        ],
    ),
]

if __name__ == "__main__":
    print([m.to_message_format() for m in ADT_19_1_ADT_EXAMPLE])
