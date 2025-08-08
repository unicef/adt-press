from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

CUADERNO3_ADT_ACTIVITY_MULTIPLE_CHOICE_2: list[messages.Example] = [
    # activity_multiple_choice_2 - cuaderno3_21
    messages.Example(
        debug_name="activity_multiple_choice_2_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/activity_multiple_choice_2/cuaderno3_21.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.activity_multiple_choice,
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-21-1",
                    type=datatypes.ExtractedTextType.chapter_title,
                    text="Esta es Elena",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-21-0",
                    type=datatypes.ExtractedTextType.chapter_title,
                    text="Actividad de Elena",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-21-2",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Lee el texto de cada libreta donde se presenta un episodio del cuento.\nElige el enunciado de la derecha que lo resume mejor.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-21-4",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Una niña, llamada Elena, a quien le encantaba jugar carreras, fue llevada por sus padres a la casa de su abuelo. Ella estaba muy disgustada.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-21-5",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="La llegada de Elena a casa del abuelo.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-21-6",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="El viaje de Elena con sus padres.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-21-7",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="El disfraz de Elena.",
                )
            ),
        ],
    ),
    messages.Example(
        debug_name="activity_multiple_choice_2_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/activity_multiple_choice_2/cuaderno3_21_section_0_0.html",
            ),
        ],
    ),
]
