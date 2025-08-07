from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks.adt_generation import adt_message_constants
from accessible_digital_textbooks.few_shot import messages

SCIENCE5_ADT_TEXT_ONLY_1_EXAMPLE: list[messages.Example] = [
    # text_only_1 - Science5_6
    messages.Example(
        debug_name="text_only_1_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=adt_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(image_path="adt_examples/text_only_1/science5_6.png"),
            messages.TextContent(text=adt_message_constants.TEXT_CONTEXT),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-10-0",
                    type=datatypes.ExtractedTextType.chapter_title,
                    text="Students as Scientists",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-10-1",
                    type=datatypes.ExtractedTextType.section_heading,
                    text="What does science look and feel like?",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-10-3",
                    type=datatypes.ExtractedTextType.section_text,
                    text="If you're reading this book, either as a student or a teacher, you're going to be digging into the “practice” of science. Probably, someone, somewhere, has made you think about this before, and so you've probably already had a chance to imagine the possibilities. Who do you picture doing science? What do they look like? What are they doing?",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-10-4",
                    type=datatypes.ExtractedTextType.section_text,
                    text="Often when we ask people to imagine this, they draw or describe people with lab coats, people with crazy hair, beakers and flasks of weird looking liquids that are bubbling and frothing. Maybe there's even an explosion. Let's be honest: Some scientists do look like this, or they look like other stereotypes: people readied with their pocket protectors and calculators, figuring out how to launch a rocket into orbit. Or maybe what comes to mind is a list of steps that you might have to check off for your science fair project to be judged; or, maybe a graph or data table with lots of numbers comes to mind.",
                )
            ),
            messages.TextContent(
                text=adt_message_constants.SECTION_TEXT_FORMAT.format(
                    id="text-10-5",
                    type=datatypes.ExtractedTextType.section_text,
                    text="So let's start over. When you imagine graphs and tables, lab coats and calculators, is that what you love? If this describes you, that's great. But if it doesn't, and that's probably true for many of us, then go ahead and dump that image of science. It's useless because it isn't you. Instead, picture yourself as a maker and doer of science. The fact is, we need scientists and citizens like you, whoever you are, because we need all of the ideas, perspectives, and creative thinkers. This includes you.",
                )
            ),
        ],
    ),
    messages.Example(
        debug_name="text_only_1_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=[
            messages.AssistantHTMLADTContent(
                html_path="adt_examples/text_only_1/science5_6.html",
            )
        ],
    ),
]

if __name__ == "__main__":
    # Just for debugging.
    print([m.to_message_format() for m in SCIENCE5_ADT_TEXT_ONLY_1_EXAMPLE])
