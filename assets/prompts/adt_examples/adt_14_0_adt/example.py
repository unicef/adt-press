from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

ADT_14_0_ADT_EXAMPLE: list[messages.Example] = [
    messages.Example(
        debug_name="adt_14_0_adt_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/adt_14_0_adt/14_0_adt.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.text_and_images,
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-13-1",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="Desarrollo sostenible ambiental",
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
                    id="text-14-0",
                    type=datatypes.ExtractedTextType.section_text,
                    text="La deforestación excesiva, la caza indiscriminada de algunas especies, la pesca intensiva (merluza, por ejemplo), la perforación de terrenos para la explotación minera (petróleo, carbón y otros minerales) son algunos ejemplos de actividades que pueden provocar daños en el planeta.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-14-1",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Los especialistas en temas ambientales proponen que las actividades humanas se desarrollen teniendo en cuenta las necesidades de las generaciones futuras.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-14-2",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Este tipo de desarrollo recibe el nombre de desarrollo sostenible.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-14-3",
                    type=datatypes.ExtractedTextType.section_text,
                    text="La Comisión Mundial del Medio Ambiente de la Organización de las Naciones Unidas (ONU) define el desarrollo sostenible como «un desarrollo que satisfaga las necesidades del presente sin poner en peligro la capacidad de las generaciones futuras para atender sus propias necesidades».",
                )
            ),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-14-0")),
            messages.ImageContent(image_path="adt_examples/adt_14_0_adt/images/14_img-14-0.jpg"),
        ],
    ),
    messages.Example(
        debug_name="adt_14_0_adt_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/adt_14_0_adt/14_0_adt.html",
            ),
        ],
    ),
]

if __name__ == "__main__":
    print([m.to_message_format() for m in ADT_14_0_ADT_EXAMPLE])
