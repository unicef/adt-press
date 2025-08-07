from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

CUADERNO5_ADT_ACTIVITY_FILL_IN_A_TABLE_1: list[messages.Example] = [
    messages.Example(
        debug_name="activity_fill_in_a_table_1_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/activity_fill_in_a_table_1/cuaderno5_19.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.activity_fill_in_a_table,
                )
            ),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-19-0")),
            messages.ImageContent(image_path="adt_examples/activity_fill_in_a_table_1/images/img-19-0.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-19-0",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="Del texto al cuadro",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-19-1",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Relee el apartado «Tipos de biomas».",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-19-2",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Completa el cuadro con la caracterización de los distintos biomas.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-19-3",
                    type=datatypes.ExtractedTextType.hint,
                    text="Puedes subrayar en el texto los datos que luego trasladarás al cuadro.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-19-4",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Tipo de Bioma",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-19-5",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Clima",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-19-6",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Vegetación",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-19-7",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Fauna",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-19-8",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Actividades Económicas",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-19-9",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Selvas",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-19-10",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Bosques",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-19-11",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Climas templados",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-19-12",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Climas fríos",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-19-13",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Praderas",
                ),
            ),
        ],
    ),
    messages.Example(
        debug_name="activity_fill_in_a_table_1_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[messages.AssistantHTMLADTContent(html_path="adt_examples/activity_fill_in_a_table_1/cuaderno5_19_section_0.html")],
    ),
]

if __name__ == "__main__":
    # Just for debugging.
    print([m.to_message_format() for m in CUADERNO5_ADT_ACTIVITY_FILL_IN_A_TABLE_1])
