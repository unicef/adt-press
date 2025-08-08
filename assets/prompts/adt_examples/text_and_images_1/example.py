from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

CUADERNO5_ADT_TEXT_AND_IMAGES_1_EXAMPLE: list[messages.Example] = [
    # Text and images 1 - Cuaderno5_26
    messages.Example(
        debug_name="text_and_images_1_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/text_and_images_1/cuaderno5_26.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.text_and_images,
                )
            ),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-26-2")),
            messages.ImageContent(image_path="adt_examples/text_and_images_1/images/26_img-26-2.png"),
            messages.TextContent(text=adt_message_constants.TEXT_CONTEXT),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-26-5",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="Comprometidos con el medio ambiente",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-26-0",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="La bióloga keniana Wangari Maathai",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-26-1",
                    type=datatypes.ExtractedTextType.image_label,
                    text="quiso combatir la pobreza que la deforestación generaba en su país",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-26-2",
                    type=datatypes.ExtractedTextType.image_label,
                    text="Para hacerlo comenzó a plantar árboles e invitó a otros a imitar la iniciativa.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-26-3",
                    type=datatypes.ExtractedTextType.image_label,
                    text="Así, con su proyecto Cinturón Verde, promovió la siembra de más de 47 millones de árboles en África. En 2004 recibió el premio Nobel de la Paz por su defensa del desarrollo sostenible y del medio ambiente.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-26-4",
                    type=datatypes.ExtractedTextType.image_label,
                    text="Foto: Martin Rowe",
                )
            ),
        ],
    ),
    messages.Example(
        debug_name="text_and_images_1_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/text_and_images_1/cuaderno5_26.html",
            ),
        ],
    ),
]

if __name__ == "__main__":
    # Just for debugging.
    print([m.to_message_format() for m in CUADERNO5_ADT_TEXT_AND_IMAGES_1_EXAMPLE])
