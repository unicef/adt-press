from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

CUADERNO3_ADT_ACTIVITY_FILL_IN_THE_BLANK_2: list[messages.Example] = [
    # activity_fill_in_the_blank_2 - cuaderno3_25
    messages.Example(
        debug_name="activity_fill_in_the_blank_2_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/activity_fill_in_the_blank_2/cuaderno3_25.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.activity_fill_in_the_blank,
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-0",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="Actividad 15",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-14",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Reemplaza los pronombres resaltados por expresiones o palabras que nombran a los personajes.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-15",
                    type=datatypes.ExtractedTextType.section_text,
                    text="A ",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-16", type=datatypes.ExtractedTextType.section_text, text="ella"
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-35",
                    type=datatypes.ExtractedTextType.activity_input_placeholder_text,
                    text="Reemplaza: ella",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-17",
                    type=datatypes.ExtractedTextType.section_text,
                    text=" le encantaba correr carreras.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-18",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Ella ",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-36",
                    type=datatypes.ExtractedTextType.activity_input_placeholder_text,
                    text="Reemplaza 'Ella'",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-19",
                    type=datatypes.ExtractedTextType.section_text,
                    text="hizo pucheros cuando ",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-20",
                    type=datatypes.ExtractedTextType.section_text,
                    text="ellos",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-37",
                    type=datatypes.ExtractedTextType.activity_input_placeholder_text,
                    text="Reemplaza: ellos",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-21",
                    type=datatypes.ExtractedTextType.section_text,
                    text=" le dijeron que tenía que ir a la casa de ",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-22", type=datatypes.ExtractedTextType.section_text, text="él"
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-23",
                    type=datatypes.ExtractedTextType.section_text,
                    text="—Tiene unos libros fabulosos —dijo ",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-24",
                    type=datatypes.ExtractedTextType.section_text,
                    text="él",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-38",
                    type=datatypes.ExtractedTextType.activity_input_placeholder_text,
                    text="Reemplaza: él",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-25",
                    type=datatypes.ExtractedTextType.section_text,
                    text=", que era el hijo del abuelo Enrique y se había puesto triste con las palabras de ",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-39",
                    type=datatypes.ExtractedTextType.activity_input_placeholder_text,
                    text="Reemplaza: ella",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-25-26",
                    type=datatypes.ExtractedTextType.section_text,
                    text="ella",
                )
            ),
        ],
    ),
    messages.Example(
        debug_name="activity_fill_in_the_blank_2_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/activity_fill_in_the_blank_2/cuaderno3_25_section_1.html",
            )
        ],
    ),
]

if __name__ == "__main__":
    # Just for debugging.
    print([m.to_message_format() for m in CUADERNO3_ADT_ACTIVITY_FILL_IN_THE_BLANK_2])
