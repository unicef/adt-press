from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

CUADERNO3_ADT_TEXT_AND_IMAGES_3_EXAMPLE: list[messages.Example] = [
    # text_and_images_3 - cuaderno3_34
    messages.Example(
        debug_name="text_and_images_3_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-34-0")),
            messages.ImageContent(image_path="adt_examples/text_and_images_3/cuaderno3_34.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.text_and_images,
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-34-0",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="La Sopa de Piedras",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-34-1",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Pedro Malasartes era un caminante pícaro y muy astuto. Un día se puso a escuchar una conversación entre varios hombres que estaban sentados en la plaza del pueblo. Hablaban de una campesina avara que vivía en una chacra cerca del río. Cada uno contaba una historia peor que otra.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-34-2",
                    type=datatypes.ExtractedTextType.section_text,
                    text="—La anciana es una tacaña. No da comida ni para los perros que cuidan su casa —contaba uno.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-34-3",
                    type=datatypes.ExtractedTextType.section_text,
                    text="—Cuando llega alguien a almorzar, cuenta los porotos antes de ponerlos en el plato —decía otro.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-34-4",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Pedro Malasartes escuchaba y pensaba. Entonces entró a la ronda de conversación:",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-34-5",
                    type=datatypes.ExtractedTextType.section_text,
                    text="—¿Quieren apostar a que ella me dará un montón de cosas y con muchas ganas?",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-34-6",
                    type=datatypes.ExtractedTextType.section_text,
                    text="—¡Estás loco! —dijeron todos—. ¡Aquella avara no da ni una sonrisa!",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-34-7",
                    type=datatypes.ExtractedTextType.section_text,
                    text="—Bueno, apuesto que a mí sí me va a dar —insistió Pedro—. ¿Cuánto quieren apostar?",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-34-8",
                    type=datatypes.ExtractedTextType.section_text,
                    text="El grupo apostó mucho, porque la conocía muy bien.",
                )
            ),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="c3_34_0")),
            messages.ImageContent(
                image_path="adt_examples/text_and_images_3/images/c3_34_0.png",
            ),
        ],
    ),
    messages.Example(
        debug_name="text_and_images_3_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/text_and_images_3/cuaderno3_34_section_0.html",
            ),
        ],
    ),
]

if __name__ == "__main__":
    # Just for debugging.
    print([m.to_message_format() for m in CUADERNO3_ADT_TEXT_AND_IMAGES_3_EXAMPLE])
