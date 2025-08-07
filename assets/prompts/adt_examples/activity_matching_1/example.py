from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

CUADERNO5_ADT_ACTIVITY_MATCHING_1: list[messages.Example] = [
    # Activity Matching 1 - Cuaderno5_30
    messages.Example(
        debug_name="activity_matching_1_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/activity_matching_1/cuaderno5_30.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.activity_matching,
                ),
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-30-0",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="La sopa de letras",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-30-16",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="Une cada una de estas palabras con su dibujo.",
                )
            ),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-30-7")),
            messages.ImageContent(image_path="adt_examples/activity_matching_1/images/30_img-30-7.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-30-8")),
            messages.ImageContent(image_path="adt_examples/activity_matching_1/images/30_img-30-8.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-30-3")),
            messages.ImageContent(image_path="adt_examples/activity_matching_1/images/30_img-30-3.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-30-5")),
            messages.ImageContent(image_path="adt_examples/activity_matching_1/images/30_img-30-5.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-30-6")),
            messages.ImageContent(image_path="adt_examples/activity_matching_1/images/30_img-30-6.png"),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-30-4")),
            messages.ImageContent(image_path="adt_examples/activity_matching_1/images/30_img-30-4.png"),
            messages.TextContent(text=adt_message_constants.TEXT_CONTEXT),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-30-17",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="bimotor",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-30-18",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="bibliobús",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-30-19",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="bilingüe",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-30-20",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="biblioteca",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-30-21",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="bicolor",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-30-22",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="bibliomanía",
                )
            ),
        ],
    ),
    messages.Example(
        debug_name="activity_matching_1_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(html_path="adt_examples/activity_matching_1/cuaderno5_30_section_2.html"),
        ],
    ),
]

if __name__ == "__main__":
    # Just for debugging.
    print([m.to_message_format() for m in CUADERNO5_ADT_ACTIVITY_MATCHING_1])
