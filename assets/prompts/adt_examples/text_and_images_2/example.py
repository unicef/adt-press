from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

CUADERNO5_ADT_TEXT_AND_IMAGES_2_EXAMPLE: list[messages.Example] = [
    # text_and_image_2 - cuaderno5_13
    messages.Example(
        debug_name="text_and_images_2_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/text_and_images_2/cuaderno5_13.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-0-1")),
            messages.ImageContent(image_path="adt_examples/text_and_images_2/0_img-0-1.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-0-2")),
            messages.ImageContent(image_path="adt_examples/text_and_images_2/0_img-0-2.png"),
            messages.TextContent(text=adt_message_constants.TEXT_CONTEXT),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-4",
                    type=datatypes.ExtractedTextType.chapter_title,
                    text="Tipos de Biomas",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-5",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="Selvas",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-7",
                    type=datatypes.ExtractedTextType.section_text,
                    text="También se las llama bosques tropicales. Se desarrollan en zonas de altas temperaturas y lluvias abundantes durante gran parte del año. Se extienden a ambos lados del ecuador en América Central, América del Sur, África, Asia y Australia. La selva amazónica es la más grande y coincide con la cuenca del río Amazonas. Su extensión aproximada es de 7.000.000 de km².",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-8",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Poseen una gran cantidad y variedad de vegetales: árboles de gran tamaño, medianos y pequeños, lianas, enredaderas, helechos, arbustos y vegetación herbácea, distribuidos en pisos (los árboles más altos forman un techo, bajo el cual las otras especies viven en forma desordenada y enmarañada). También presentan una gran cantidad y variedad de animales, por ejemplo, monos, reptiles, aves, insectos y mamíferos depredadores.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-9",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Las actividades económicas están vinculadas con la explotación de recursos forestales y mineros. La deforestación o la tala de especies provoca graves consecuencias, por ejemplo, pérdida de la biodiversidad, cambios climáticos globales, desaparición de especies animales y vegetales, y pérdida de los suelos.",
                )
            ),
            messages.TextContent(text=adt_message_constants.TEXT_CONTEXT),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-11",
                    type=datatypes.ExtractedTextType.image_caption,
                    text="Selva amazónica, Brasil",
                )
            ),
            messages.TextContent(text=adt_message_constants.TEXT_CONTEXT),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-13",
                    type=datatypes.ExtractedTextType.image_caption,
                    text="Selva ecuatoriana",
                )
            ),
        ],
    ),
    messages.Example(
        debug_name="text_and_images_2_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[messages.AssistantHTMLADTContent(html_path="adt_examples/text_and_images_2/cuaderno5_13.html")],
    ),
]

if __name__ == "__main__":
    # Just for debugging.
    print([m.to_message_format() for m in CUADERNO5_ADT_TEXT_AND_IMAGES_2_EXAMPLE])
