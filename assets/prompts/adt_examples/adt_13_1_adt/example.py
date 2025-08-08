from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

ADT_13_1_ADT_EXAMPLE: list[messages.Example] = [
    messages.Example(
        debug_name="adt_13_1_adt_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/adt_13_1_adt/13_1_adt.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.text_only,
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-0",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="Los Biomas",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-10",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="LOS BIOMAS Y LA ACCIÓN DEL HOMBRE",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-11",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Los seres humanos son parte de los seres vivos que habitan los biomas.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-12",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Para satisfacer sus necesidades, los humanos modifican el medio natural.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-13",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Por ejemplo, cultivan campos, construyen edificios, puentes, autopistas, entre otras transformaciones.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-14",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Los especialistas señalan que actualmente ya no existen ambientes completamente naturales, es decir, que no hayan sido modificados por la acción humana.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-15",
                    type=datatypes.ExtractedTextType.section_text,
                    text="La transformación de la naturaleza es imprescindible para la vida humana, pero muchas veces se realiza sin tener los cuidados necesarios y se producen daños que pueden ser irreparables.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-16",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Biomas del mundo",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-17",
                    type=datatypes.ExtractedTextType.boxed_text,
                    text="El clima y el relieve tienen gran importancia en la formación de los biomas.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-18",
                    type=datatypes.ExtractedTextType.boxed_text,
                    text="Por ejemplo, algunas cadenas montañosas son como enormes paredones interpuestos en el recorrido de los vientos húmedos provenientes del océano.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-19",
                    type=datatypes.ExtractedTextType.boxed_text,
                    text="Al chocar contra la montaña, estos vientos descargan su humedad en la ladera enfrentada al mar, mientras que la otra ladera es árida.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-20",
                    type=datatypes.ExtractedTextType.boxed_text,
                    text="Asimismo, la altura es un factor determinante: en las montañas, los biomas se distribuyen en pisos, según la altura.",
                )
            ),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-13-1")),
            messages.ImageContent(image_path="adt_examples/adt_13_1_adt/images/13_img-13-1-v2.jpg"),
        ],
    ),
    messages.Example(
        debug_name="adt_13_1_adt_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/adt_13_1_adt/13_1_adt.html",
            ),
        ],
    ),
]

if __name__ == "__main__":
    print([m.to_message_format() for m in ADT_13_1_ADT_EXAMPLE])
