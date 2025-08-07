from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

LIVINGURUGUAY1_ADT_ACTIVITY_TRUE_FALSE_1: list[messages.Example] = [
    # True False Activity 1 - Lu1_83
    messages.Example(
        debug_name="activity_true_false_1_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/activity_true_false_1/lu1_83.png"),
            messages.TextContent(
                text=adt_message_constants.SECTION_TYPE_CONTEXT.format(
                    section_type=datatypes.SectionType.activity_true_false,
                ),
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-81-3",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="True or false activity",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-81-0",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Now, Johnny is talking to Emma about the conversation he had with Lua.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-81-1",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Read what Johnny says to Lua and check whether he is",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-81-2",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="right",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-81-4",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="wrong",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-81-5",
                    type=datatypes.ExtractedTextType.instruction_text,
                    text="Correct the wrong information",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-81-7",
                    type=datatypes.ExtractedTextType.activity_option,
                    text="1. Mr. Simon has short whiskers.",
                )
            ),
        ],
    ),
    messages.Example(
        debug_name="activity_true_false_1_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(html_path="adt_examples/activity_true_false_1/livinguruguay1_83_section_1.html"),
        ],
    ),
]

if __name__ == "__main__":
    # Just for debugging.
    print([m.to_message_format() for m in LIVINGURUGUAY1_ADT_ACTIVITY_TRUE_FALSE_1])
