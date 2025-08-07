from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

ADT_12_ADT_EXAMPLE: list[messages.Example] = [
    messages.Example(
        debug_name="adt_12_adt_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/adt_12_adt/12_adt.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.text_and_images,
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-12-0",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="A ciencia cierta",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-12-1",
                    type=datatypes.ExtractedTextType.section_text,
                    text="La explicación",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-12-7",
                    type=datatypes.ExtractedTextType.image_label,
                    text="TUNDRA",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-12-8",
                    type=datatypes.ExtractedTextType.image_label,
                    text="TAIGA",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-12-5",
                    type=datatypes.ExtractedTextType.image_label,
                    text="DESIERTO",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-12-4",
                    type=datatypes.ExtractedTextType.image_label,
                    text="BOSQUE TEMPLADO",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-12-6",
                    type=datatypes.ExtractedTextType.image_label,
                    text="ESTEPA",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-12-2",
                    type=datatypes.ExtractedTextType.image_label,
                    text="SELVA TROPICAL",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-12-14",
                    type=datatypes.ExtractedTextType.image_label,
                    text="PRADERA",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-12-20",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Piensa sobre estas preguntas...",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-12-9",
                    type=datatypes.ExtractedTextType.boxed_text,
                    text="¿En qué se diferencia la selva tropical del desierto? ¿Y la tundra de la pradera?",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-12-10",
                    type=datatypes.ExtractedTextType.boxed_text,
                    text="¿Y cuál es la diferencia entre un bosque templado y un bosque tropical?",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-12-11",
                    type=datatypes.ExtractedTextType.boxed_text,
                    text="¿Qué semejanzas tienen la pradera y la sabana?",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-12-12",
                    type=datatypes.ExtractedTextType.boxed_text,
                    text="¿Por qué algunos seres vivos habitan en una región y no en otra?",
                )
            ),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-12-3")),
            messages.ImageContent(image_path="adt_examples/adt_12_adt/images/12_img-12-3.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-12-2")),
            messages.ImageContent(image_path="adt_examples/adt_12_adt/images/12_img-12-2.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-12-5")),
            messages.ImageContent(image_path="adt_examples/adt_12_adt/images/12_img-12-5.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-12-6")),
            messages.ImageContent(image_path="adt_examples/adt_12_adt/images/12_img-12-6.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-12-4")),
            messages.ImageContent(image_path="adt_examples/adt_12_adt/images/12_img-12-4.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-12-1")),
            messages.ImageContent(image_path="adt_examples/adt_12_adt/images/12_img-12-1.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-12-7")),
            messages.ImageContent(image_path="adt_examples/adt_12_adt/images/12_img-12-7.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-12-9")),
            messages.ImageContent(image_path="adt_examples/adt_12_adt/images/12_img-12-9.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-12-8")),
            messages.ImageContent(image_path="adt_examples/adt_12_adt/images/12_img-12-8.png"),
        ],
    ),
    messages.Example(
        debug_name="adt_12_adt_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/adt_12_adt/12_adt.html",
            ),
        ],
    ),
]

if __name__ == "__main__":
    print([m.to_message_format() for m in ADT_12_ADT_EXAMPLE])
