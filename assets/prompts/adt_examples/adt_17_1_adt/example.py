from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

ADT_17_1_ADT_EXAMPLE: list[messages.Example] = [
    messages.Example(
        debug_name="adt_17_1_adt_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/adt_17_1_adt/17_1_adt.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.activity_sorting,
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-0",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="Fuente: el manual de estudio",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-6",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Si tienes que estudiar estos temas, ¿en qué estantes de la biblioteca buscas los libros?",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-7",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Únelos con el área que corresponde.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-8",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="La imagen digital",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-9",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="Homónimos",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-10",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="Ríos del Uruguay",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-11",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="Los biomas",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-17",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="Las clases de polígonos",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-18",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="La Revolución oriental",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-19",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="Los mitos y las leyendas",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-20",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="El aparato digestivo",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-12",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="Lengua y Literatura",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-13",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="Ciencias Sociales",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-14",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="Ciencias Naturales",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-15",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="Matemática",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-16",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="Artes Visuales",
                )
            ),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-17-1")),
            messages.ImageContent(image_path="adt_examples/adt_17_1_adt/images/17_img-17-1.png"),
        ],
    ),
    messages.Example(
        debug_name="adt_17_1_adt_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/adt_17_1_adt/17_1_adt.html",
            ),
        ],
    ),
]

if __name__ == "__main__":
    print([m.to_message_format() for m in ADT_17_1_ADT_EXAMPLE])
