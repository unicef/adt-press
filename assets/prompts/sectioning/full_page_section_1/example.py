import json
from pydantic_core import to_jsonable_python
from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks import extraction_message_constants, task_datatypes
from accessible_digital_textbooks.few_shot import example_datatypes, messages

"""
Reference text extracted from page.

39,text-39-0,es,Elige las expresiones que te permitan completar los enunciados de abajo.,instruction_text,0,activity_fill_in_the_blank,en
39,text-39-1,es,unas piedras del suelo,activity_option,0,activity_fill_in_the_blank,en
39,text-39-2,es,algunas papas y boniatos,activity_option,0,activity_fill_in_the_blank,en
39,text-39-3,es,algunos condimentos,activity_option,0,activity_fill_in_the_blank,en
39,text-39-4,es,"cebolla, perejil, sal y ajo",activity_option,0,activity_fill_in_the_blank,en
39,text-39-5,es,en la vasija,activity_option,0,activity_fill_in_the_blank,en
39,text-39-6,es,en la cazuela,activity_option,0,activity_fill_in_the_blank,en
39,text-39-7,es,en la cacerola,activity_option,0,activity_fill_in_the_blank,en
39,text-39-8,es,en la olla,activity_option,0,activity_fill_in_the_blank,en
39,text-39-9,es,reluciente.,activity_option,0,activity_fill_in_the_blank,en
39,text-39-10,es,lustroso.,activity_option,0,activity_fill_in_the_blank,en
39,text-39-11,es,curado.,activity_option,0,activity_fill_in_the_blank,en
39,text-39-12,es,esmaltada.,activity_option,0,activity_fill_in_the_blank,en
39,text-39-13,es,los,activity_option,0,activity_fill_in_the_blank,en
39,text-39-14,es,las,activity_option,0,activity_fill_in_the_blank,en
39,text-39-15,es,las,activity_option,0,activity_fill_in_the_blank,en
39,text-39-16,es,los,activity_option,0,activity_fill_in_the_blank,en
39,text-39-17,es,Pedro Malasartes tomó,instruction_text,1,activity_fill_in_the_blank,en
39,text-39-18,es,algunos condimentos,activity_option,1,activity_fill_in_the_blank,en
39,text-39-19,es,y,other,1,activity_fill_in_the_blank,en
39,text-39-20,es,los,activity_option,1,activity_fill_in_the_blank,en
39,text-39-21,es,puso,standalone_text,1,activity_fill_in_the_blank,en
39,text-39-22,es,en una olla,activity_option,1,activity_fill_in_the_blank,en
39,text-39-23,es,de metal,activity_option,1,activity_fill_in_the_blank,en
39,text-39-24,es,reluciente.,activity_option,1,activity_fill_in_the_blank,en
39,text-39-25,es,Pedro Malasartes tomó,instruction_text,2,activity_fill_in_the_blank,en
39,text-39-26,es,arrojó,standalone_text,2,activity_fill_in_the_blank,en
39,text-39-27,es,de barro,activity_option,2,activity_fill_in_the_blank,en
39,text-39-28,es,Pedro Malasartes tomó,instruction_text,3,activity_fill_in_the_blank,en
39,text-39-29,es,colocó,standalone_text,3,activity_fill_in_the_blank,en
39,text-39-30,es,de cerámica,activity_option,3,activity_fill_in_the_blank,en
39,text-39-31,es,Con las expresiones que quedaron sin tachar escribe el último enunciado.,instruction_text,4,activity_fill_in_the_blank,en
"""

PAGE_TEXT: list[datatypes.BaseText] = [
    datatypes.BaseText(
        id="text-39-0",
        text="Elige las expresiones que te permitan completar los enunciados de abajo.",
    ),
    datatypes.BaseText(
        id="text-39-1",
        text="unas piedras del suelo",
    ),
    datatypes.BaseText(
        id="text-39-2",
        text="algunas papas y boniatos",
    ),
    datatypes.BaseText(
        id="text-39-3",
        text="algunos condimentos",
    ),
    datatypes.BaseText(
        id="text-39-4",
        text="cebolla, perejil, sal y ajo",
    ),
    datatypes.BaseText(
        id="text-39-5",
        text="en la vasija",
    ),
    datatypes.BaseText(
        id="text-39-6",
        text="en la cazuela",
    ),
    datatypes.BaseText(
        id="text-39-7",
        text="en la cacerola",
    ),
    datatypes.BaseText(
        id="text-39-8",
        text="en la olla",
    ),
    datatypes.BaseText(
        id="text-39-9",
        text="reluciente.",
    ),
    datatypes.BaseText(
        id="text-39-10",
        text="lustroso.",
    ),
    datatypes.BaseText(
        id="text-39-11",
        text="curado.",
    ),
    datatypes.BaseText(
        id="text-39-12",
        text="esmaltada.",
    ),
    datatypes.BaseText(
        id="text-39-15",
        text="las",
    ),
    datatypes.BaseText(
        id="text-39-16",
        text="los",
    ),
    datatypes.BaseText(
        id="text-39-17",
        text="Pedro Malasartes tomó",
    ),
    datatypes.BaseText(
        id="text-39-18",
        text="algunos condimentos",
    ),
    datatypes.BaseText(
        id="text-39-19",
        text="y",
    ),
    datatypes.BaseText(
        id="text-39-20",
        text="los",
    ),
    datatypes.BaseText(
        id="text-39-21",
        text="puso",
    ),
    datatypes.BaseText(
        id="text-39-22",
        text="en una olla",
    ),
    datatypes.BaseText(
        id="text-39-23",
        text="de metal",
    ),
    datatypes.BaseText(
        id="text-39-24",
        text="reluciente.",
    ),
    datatypes.BaseText(
        id="text-39-25",
        text="Pedro Malasartes tomó",
    ),
    datatypes.BaseText(
        id="text-39-26",
        text="arrojó",
    ),
    datatypes.BaseText(
        id="text-39-27",
        text="de barro",
    ),
    datatypes.BaseText(
        id="text-39-28",
        text="Pedro Malasartes tomó",
    ),
    datatypes.BaseText(
        id="text-39-29",
        text="colocó",
    ),
    datatypes.BaseText(
        id="text-39-30",
        text="de cerámica",
    ),
    datatypes.BaseText(
        id="text-39-31",
        text="Con las expresiones que quedaron sin tachar escribe el último enunciado.",
    ),
]

ASSISTANT_RESPONSE = example_datatypes.SectioningResponseFormatExample(
    reasoning="",
    data=[
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-0",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-1",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-2",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-3",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-4",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-5",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-6",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-7",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-8",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-9",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-10",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-11",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-12",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-15",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-16",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-17",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-18",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-19",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-20",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-21",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-22",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-23",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-24",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-25",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-26",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-27",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-28",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-29",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-30",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_fill_in_the_blank,
            id="text-39-31",
        ),
    ],
)

CUADERNO_3_38_EXAMPLE: list[messages.Example] = [
    messages.Example(
        debug_name="cuaderno_3_38_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=extraction_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(
                image_path="sectioning_examples/full_page_section_1/cuaderno3_38.png"
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
        debug_name="cuaderno_3_38_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=ASSISTANT_RESPONSE,
    ),
]
