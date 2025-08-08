from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

CUADERNO3_ADT_ACTIVITY_SORTING_1: list[messages.Example] = [
    # Activity Sorting 1 - Cuaderno3_28
    messages.Example(
        debug_name="activity_sorting_1_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/activity_sorting_1/cuaderno3_27.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.activity_sorting,
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-28-0",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="Actividad de clasificación",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-28-2",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="Fuentes de luz",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-28-0",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Relee el artículo «La luz y la sombra».",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-28-1",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Completa el cuadro con las palabras de la lista.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-28-5",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="sol",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-28-6",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="estrellas",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-28-7",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="vela",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-28-8",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="linterna",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-28-9",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="fuego",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-28-10",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="luciérnagas",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-28-11",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="rayos",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-28-12",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="lámpara eléctrica",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-28-3",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Natural",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-28-4",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Artificial",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="afitb_0_0",
                    type=datatypes.ExtractedTextType.section_text,
                    text="",  # Feedback is dynamic and initially empty
                )
            ),
        ],
    ),
    messages.Example(
        debug_name="activity_sorting_1_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/activity_sorting_1/cuaderno3_27_section_0.html",
            ),
        ],
    ),
]

if __name__ == "__main__":
    # Just for debugging.
    print([m.to_message_format() for m in CUADERNO3_ADT_ACTIVITY_SORTING_1])
