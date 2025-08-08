from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

ADT_13_0_ADT_EXAMPLE: list[messages.Example] = [
    messages.Example(
        debug_name="adt_13_0_adt_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/adt_13_0_adt/13_0_adt.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.text_and_images,
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
                    id="text-13-1",
                    type=datatypes.ExtractedTextType.section_text,
                    text="La vida en nuestro planeta depende de la energía del sol, de la disponibilidad de agua y de la existencia de nutrientes en los suelos, entre otros factores.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-2",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Pero no todas las regiones del mundo poseen las mismas condiciones.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-3",
                    type=datatypes.ExtractedTextType.section_text,
                    text="En cada región del planeta existen distintos climas, formas de relieve y tipos de suelo, que generan las condiciones ambientales para el desarrollo de la vida en ese lugar.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-4",
                    type=datatypes.ExtractedTextType.section_text,
                    text="En cada región vive un conjunto de seres adaptados al lugar que habitan.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-5",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Por ejemplo, en el desierto, tanto las plantas como los animales están adaptados a la escasa disponibilidad del agua.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-6",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Los seres vivos que habitan una región también se relacionan entre sí, por ejemplo, unos son alimento de otros.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-7",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Cada una de las regiones en las cuales los seres vivos interactúan entre sí y con el lugar en el que viven se denomina ecosistema.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-8",
                    type=datatypes.ExtractedTextType.section_text,
                    text="En la Tierra encontramos ecosistemas similares en lugares muy distantes entre sí.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-9",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Por ejemplo, hay selvas o bosques tropicales en el centro de África, el norte de Sudamérica y el sudoeste de Asia.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-21",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Los ecosistemas pueden clasificarse en distintos tipos denominadosbiomas.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-22",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Por ejemplo: selvas, desiertos, bosques o praderas.",
                )
            ),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-13-2")),
            messages.ImageContent(image_path="adt_examples/adt_13_0_adt/images/13_img-13-2.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-13-4")),
            messages.ImageContent(image_path="adt_examples/adt_13_0_adt/images/13_img-13-4.jpg"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-13-5")),
            messages.ImageContent(image_path="adt_examples/adt_13_0_adt/images/13_img-13-5.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-13-6")),
            messages.ImageContent(image_path="adt_examples/adt_13_0_adt/images/13_img-13-6.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-13-3")),
            messages.ImageContent(image_path="adt_examples/adt_13_0_adt/images/13_img-13-3.png"),
        ],
    ),
    messages.Example(
        debug_name="adt_13_0_adt_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/adt_13_0_adt/13_0_adt.html",
            ),
        ],
    ),
]

if __name__ == "__main__":
    print([m.to_message_format() for m in ADT_13_0_ADT_EXAMPLE])
