import json
from pydantic_core import to_jsonable_python

from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks import extraction_message_constants, task_datatypes
from accessible_digital_textbooks.few_shot import example_datatypes, messages

"""
Reference text extracted from page.

105,text-105-31,en,UNIT 5,section_heading,3,other,es
105,text-105-6,en,A- noodles,activity_option,0,activity_other,es
105,text-105-5,en,1,instruction_text,0,activity_other,es
105,text-105-4,en,Circle the odd one out.,instruction_text,0,activity_other,es
105,text-105-3,en,One of them is different.,instruction_text,0,activity_other,es
105,text-105-2,en,I’ll give you four words or phrases.,instruction_text,0,activity_other,es
105,text-105-1,en,Let’s play a game.,instruction_text,0,activity_other,es
105,text-105-0,en,The importance of snacks,section_heading,0,activity_other,es
105,text-105-7,en,B- salad,activity_option,0,activity_other,es
105,text-105-32,en,Fantastic Food,section_heading,3,other,es
105,text-105-9,en,D- BBQ,activity_option,0,activity_other,es
105,text-105-10,en,2,instruction_text,0,activity_other,es
105,text-105-11,en,A- an apple,activity_option,0,activity_other,es
105,text-105-12,en,B- steak,activity_option,0,activity_other,es
105,text-105-13,en,C- granola,activity_option,0,activity_other,es
105,text-105-14,en,D- raisins,activity_option,0,activity_other,es
105,text-105-8,en,C- peanut,activity_option,0,activity_other,es
105,text-105-16,en,A-cherry tomatoes,activity_option,0,activity_other,es
105,text-105-15,en,3,instruction_text,0,activity_other,es
105,text-105-28,en,Choose 3 reasons you believe as the most important ones.,instruction_text,2,activity_open_ended_answer,es
105,text-105-27,en,Get with a partner and discuss the reasons all your classmates gave.,instruction_text,2,activity_open_ended_answer,es
105,text-105-26,en,"For example, I eat granola between meals.",standalone_text,1,activity_open_ended_answer,es
105,text-105-25,en,Why do you think that snacks are important?,instruction_text,1,activity_open_ended_answer,es
105,text-105-24,en,The other day I was reading about the importance of snacks in our lives.,standalone_text,1,activity_open_ended_answer,es
105,text-105-30,en,#livingUruguay1,footer_text,3,other,es
105,text-105-22,en,Which food do you get for lunch or dinner?,instruction_text,1,activity_open_ended_answer,es
105,text-105-21,en,How can you classify or differentiate food?,instruction_text,1,activity_open_ended_answer,es
105,text-105-20,en,About you…,section_heading,1,activity_open_ended_answer,es
105,text-105-19,en,D-cereal bar,activity_option,0,activity_other,es
105,text-105-18,en,C-stew,activity_option,0,activity_other,es
105,text-105-17,en,B-sliced bananas,activity_option,0,activity_other,es
105,text-105-23,en,Which food do you get between meals?,instruction_text,1,activity_open_ended_answer,es
"""

PAGE_TEXT: list[datatypes.BaseText] = [
    datatypes.BaseText(
        id="text-105-0",
        text="The importance of snacks",
    ),
    datatypes.BaseText(
        id="text-105-1",
        text="Let’s play a game.",
    ),
    datatypes.BaseText(
        id="text-105-2",
        text="I’ll give you four words or phrases.",
    ),
    datatypes.BaseText(
        id="text-105-3",
        text="One of them is different.",
    ),
    datatypes.BaseText(
        id="text-105-4",
        text="Circle the odd one out.",
    ),
    datatypes.BaseText(
        id="text-105-5",
        text="1",
    ),
    datatypes.BaseText(
        id="text-105-6",
        text="A- noodles",
    ),
    datatypes.BaseText(
        id="text-105-7",
        text="B- salad",
    ),
    datatypes.BaseText(
        id="text-105-8",
        text="C- peanut",
    ),
    datatypes.BaseText(
        id="text-105-9",
        text="D- BBQ",
    ),
    datatypes.BaseText(
        id="text-105-10",
        text="2",
    ),
    datatypes.BaseText(
        id="text-105-11",
        text="A- an apple",
    ),
    datatypes.BaseText(
        id="text-105-12",
        text="B- steak",
    ),
    datatypes.BaseText(
        id="text-105-13",
        text="C- granola",
    ),
    datatypes.BaseText(
        id="text-105-14",
        text="D- raisins",
    ),
    datatypes.BaseText(
        id="text-105-15",
        text="3",
    ),
    datatypes.BaseText(
        id="text-105-16",
        text="A-cherry tomatoes",
    ),
    datatypes.BaseText(
        id="text-105-17",
        text="B-sliced bananas",
    ),
    datatypes.BaseText(
        id="text-105-18",
        text="C-stew",
    ),
    datatypes.BaseText(
        id="text-105-19",
        text="D-cereal bar",
    ),
    datatypes.BaseText(
        id="text-105-20",
        text="About you…",
    ),
    datatypes.BaseText(
        id="text-105-21",
        text="How can you classify or differentiate food?",
    ),
    datatypes.BaseText(
        id="text-105-22",
        text="Which food do you get for lunch or dinner?",
    ),
    datatypes.BaseText(
        id="text-105-23",
        text="Which food do you get between meals?",
    ),
    datatypes.BaseText(
        id="text-105-24",
        text="The other day I was reading about the importance of snacks in our lives.",
    ),
    datatypes.BaseText(
        id="text-105-25",
        text="Why do you think that snacks are important?",
    ),
    datatypes.BaseText(
        id="text-105-26",
        text="For example, I eat granola between meals.",
    ),
    datatypes.BaseText(
        id="text-105-27",
        text="Get with a partner and discuss the reasons all your classmates gave.",
    ),
    datatypes.BaseText(
        id="text-105-28",
        text="Choose 3 reasons you believe as the most important ones.",
    ),
    datatypes.BaseText(
        id="text-105-30",
        text="#livingUruguay1",
    ),
    datatypes.BaseText(
        id="text-105-32",
        text="UNIT 5",
    ),
]

ASSISTANT_RESPONSE = example_datatypes.SectioningResponseFormatExample(
    reasoning="",
    data=[
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-0",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-1",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-2",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-3",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-4",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-5",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-6",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-7",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-8",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-9",
        ),
        task_datatypes.SectionData(
            section_id=1,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-0",
        ),
        task_datatypes.SectionData(
            section_id=1,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-1",
        ),
        task_datatypes.SectionData(
            section_id=1,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-2",
        ),
        task_datatypes.SectionData(
            section_id=1,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-3",
        ),
        task_datatypes.SectionData(
            section_id=1,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-4",
        ),
        task_datatypes.SectionData(
            section_id=1,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-10",
        ),
        task_datatypes.SectionData(
            section_id=1,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-11",
        ),
        task_datatypes.SectionData(
            section_id=1,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-12",
        ),
        task_datatypes.SectionData(
            section_id=1,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-13",
        ),
        task_datatypes.SectionData(
            section_id=1,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-14",
        ),
        task_datatypes.SectionData(
            section_id=2,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-0",
        ),
        task_datatypes.SectionData(
            section_id=2,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-1",
        ),
        task_datatypes.SectionData(
            section_id=2,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-2",
        ),
        task_datatypes.SectionData(
            section_id=2,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-3",
        ),
        task_datatypes.SectionData(
            section_id=2,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-4",
        ),
        task_datatypes.SectionData(
            section_id=2,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-15",
        ),
        task_datatypes.SectionData(
            section_id=2,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-16",
        ),
        task_datatypes.SectionData(
            section_id=2,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-17",
        ),
        task_datatypes.SectionData(
            section_id=2,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-18",
        ),
        task_datatypes.SectionData(
            section_id=2,
            section_type=datatypes.SectionType.activity_multiple_choice,
            id="text-105-19",
        ),
        task_datatypes.SectionData(
            section_id=3,
            section_type=datatypes.SectionType.activity_open_ended_answer,
            id="text-105-20",
        ),
        task_datatypes.SectionData(
            section_id=3,
            section_type=datatypes.SectionType.activity_open_ended_answer,
            id="text-105-21",
        ),
        task_datatypes.SectionData(
            section_id=3,
            section_type=datatypes.SectionType.activity_open_ended_answer,
            id="text-105-22",
        ),
        task_datatypes.SectionData(
            section_id=3,
            section_type=datatypes.SectionType.activity_open_ended_answer,
            id="text-105-23",
        ),
        task_datatypes.SectionData(
            section_id=4,
            section_type=datatypes.SectionType.activity_open_ended_answer,
            id="text-105-24",
        ),
        task_datatypes.SectionData(
            section_id=4,
            section_type=datatypes.SectionType.activity_open_ended_answer,
            id="text-105-25",
        ),
        task_datatypes.SectionData(
            section_id=4,
            section_type=datatypes.SectionType.activity_open_ended_answer,
            id="text-105-26",
        ),
        task_datatypes.SectionData(
            section_id=4,
            section_type=datatypes.SectionType.activity_open_ended_answer,
            id="img-105-1",
        ),
        task_datatypes.SectionData(
            section_id=5,
            section_type=datatypes.SectionType.activity_open_ended_answer,
            id="text-105-20",
        ),
        task_datatypes.SectionData(
            section_id=5,
            section_type=datatypes.SectionType.activity_open_ended_answer,
            id="text-105-27",
        ),
        task_datatypes.SectionData(
            section_id=5,
            section_type=datatypes.SectionType.activity_open_ended_answer,
            id="text-105-28",
        ),
        task_datatypes.SectionData(
            section_id=6,
            section_type=datatypes.SectionType.other,
            id="text-105-30",
        ),
        task_datatypes.SectionData(
            section_id=6,
            section_type=datatypes.SectionType.other,
            id="text-105-32",
        ),
    ],
)


LIVING_URUGUAY_1_107_EXAMPLE: list[messages.Example] = [
    messages.Example(
        debug_name="living_uruguay_1_107_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=extraction_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(
                image_path="sectioning_examples/multiple_activities_1/livinguruguay1_107.png"
            ),
            messages.TextContent(
                text=extraction_message_constants.IMAGE_ID_PREFACE.format(id="img-105-1")
            ),
            messages.ImageContent(
                image_path="sectioning_examples/multiple_activities_1/105_img-105-1.png"
            ),
            messages.TextContent(
                text=extraction_message_constants.SECTIONING_TEXT_IDS_PREFACE.format(
                    text_ids=[text.id for text in PAGE_TEXT]
                )
            ),
            messages.TextContent(text=extraction_message_constants.SECTIONING_TEXT_PREFACE),
            messages.TextContent(text=json.dumps(PAGE_TEXT, default=to_jsonable_python)),
            messages.TextContent(
                text=extraction_message_constants.SECTIONING_USER_REQUEST,
            ),
        ],
    ),
    messages.Example(
        debug_name="living_uruguay_1_107_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=ASSISTANT_RESPONSE,
    ),
]
