from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

ADT_10_0_ADT_EXAMPLE: list[messages.Example] = [
    messages.Example(
        debug_name="adt_10_0_adt_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/adt_10_0_adt/10_0_adt.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.activity_fill_in_a_table,
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-10-2",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="Conociendo a tus mejores amigos",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-10-0",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="Me gustaría conocer a tus mejores amigos.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-10-1",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Piensa en uno de tus mejores amigos o amigas y completa su información.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-10-3",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Se llama",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-10-4",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Sus amigos lo/la llaman",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-10-5",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Juega siempre con",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-10-6",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Tiene el cabello",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-10-7",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="y los ojos",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-10-8",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Lo que más le gusta es",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-10-9",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Le desagrada",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-10-10",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Cuando está feliz",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-10-11",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Si está triste",
                )
            ),
        ],
    ),
    messages.Example(
        debug_name="adt_10_0_adt_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/adt_10_0_adt/10_0_adt.html",
            ),
        ],
    ),
]

if __name__ == "__main__":
    print([m.to_message_format() for m in ADT_10_0_ADT_EXAMPLE])
