from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

LIVINGURUGUAY1_ADT_ACTIVITY_MULTIPLE_CHOICE_1: list[messages.Example] = [
    # multi_choice_1 - livinguruguay1_107
    messages.Example(
        debug_name="multi_choice_1_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/activity_multiple_choice_1/livinguruguay1_107.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.activity_multiple_choice,
                ),
            ),
            messages.TextContent(text=adt_message_constants.IMAGE_ID_CONTEXT.format(id="img-105-1")),
            messages.ImageContent(image_path="adt_examples/activity_multiple_choice_1/images/105_img-105-1.png"),
            messages.TextContent(text=adt_message_constants.TEXT_CONTEXT),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-105-1",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="The important of snacks",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-105-2",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Let's play a game.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-105-3",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="I'll give you four words or phrases. One of them is different. Circle the odd one out.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-105-5",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="A - noodles",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-105-6",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="B - salad",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-105-7",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="C - peanut",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-105-8",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="D - BBQ",
                )
            ),
        ],
    ),
    messages.Example(
        debug_name="multi_choice_1_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[messages.AssistantHTMLADTContent(html_path="adt_examples/activity_multiple_choice_1/livinguruguay1_107_section_0_0.html")],
    ),
]

if __name__ == "__main__":
    # Just for debugging.
    print([m.to_message_format() for m in LIVINGURUGUAY1_ADT_ACTIVITY_MULTIPLE_CHOICE_1])
