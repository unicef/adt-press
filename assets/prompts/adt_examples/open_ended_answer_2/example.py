from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

CUADERNO3_ADT_ACTIVITY_OPEN_ENDED_ANSWER_2: list[messages.Example] = [
    # open_ended_answer_2 - cuaderno3_17
    messages.Example(
        debug_name="open_ended_answer_2_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/open_ended_answer_2/cuaderno3_17.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.activity_open_ended_answer,
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-0",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="Esta es Elena.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-7",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Escribe un retrato de Elena utilizando la información del esquema y otros datos del cuento.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-8",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Elena es una niña que vive con su familia.",
                )
            ),
            # "Tiene" as section text followed by open-ended input
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-9",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Tiene:",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-34",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="Descripción de lo que tiene Elena",
                )
            ),
            # "Usa" as section text followed by open-ended input
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-10",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Usa:",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-35",
                    type=datatypes.ExtractedTextType.activity_input_placeholder_text,
                    text="Descripción de lo que usa Elena",
                )
            ),
            # "Cuando corre" as section text followed by open-ended input
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-11",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Cuando corre:",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-36",
                    type=datatypes.ExtractedTextType.activity_input_placeholder_text,
                    text="Descripción de lo que pasa cuando corre Elena",
                )
            ),
            # "Le gusta" as section text followed by open-ended input
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-12",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Le gusta:",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-17-37",
                    type=datatypes.ExtractedTextType.activity_input_placeholder_text,
                    text="Descripción de lo que le gusta a Elena",
                )
            ),
        ],
    ),
    messages.Example(
        debug_name="open_ended_answer_2_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/open_ended_answer_2/cuaderno3_17_section_1.html",
            )
        ],
    ),
]

if __name__ == "__main__":
    # Just for debugging.
    print([m.to_message_format() for m in CUADERNO3_ADT_ACTIVITY_OPEN_ENDED_ANSWER_2])
