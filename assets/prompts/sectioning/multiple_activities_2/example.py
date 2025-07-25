import json
from pydantic_core import to_jsonable_python
from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks import extraction_message_constants, task_datatypes
from accessible_digital_textbooks.few_shot import example_datatypes, messages

"""
Reference text extracted from page.

28,text-28-2,es,FUENTES DE LUZ,section_heading,0,activity_fill_in_a_table,en
28,text-28-14,es,TIPO DE CUERPO,section_heading,1,activity_fill_in_a_table,en
28,text-28-15,es,CARACTERÍSTICAS,section_heading,1,activity_fill_in_a_table,en
28,text-28-6,es,estrellas,activity_option,0,activity_fill_in_a_table,en
28,text-28-0,es,Relee el artículo «La luz y la sombra».,instruction_text,0,activity_fill_in_a_table,en
28,text-28-1,es,Completa el cuadro con las palabras de la lista.,instruction_text,0,activity_fill_in_a_table,en
28,text-28-3,es,NATURAL,section_heading,0,activity_fill_in_a_table,en
28,text-28-4,es,ARTIFICIAL,section_heading,0,activity_fill_in_a_table,en
28,text-28-5,es,sol,activity_option,0,activity_fill_in_a_table,en
28,text-28-8,es,linterna,activity_option,0,activity_fill_in_a_table,en
28,text-28-7,es,vela,activity_option,0,activity_fill_in_a_table,en
28,text-28-10,es,luciérnagas,activity_option,0,activity_fill_in_a_table,en
28,text-28-11,es,rayos,activity_option,0,activity_fill_in_a_table,en
28,text-28-12,es,lámpara eléctrica,activity_option,0,activity_fill_in_a_table,en
28,text-28-13,es,Completa el cuadro que resume información sobre el tema.,instruction_text,1,activity_fill_in_a_table,en
28,text-28-19,es,vidrio esmerilado,section_text,1,activity_fill_in_a_table,en
28,text-28-18,es,Permiten el paso de la luz y se puede ver a través de ellos con nitidez.,section_text,1,activity_fill_in_a_table,en
28,text-28-17,es,opaco,section_text,1,activity_fill_in_a_table,en
28,text-28-16,es,EJEMPLOS,section_heading,1,activity_fill_in_a_table,en
28,text-28-9,es,fuego,activity_option,0,activity_fill_in_a_table,en
"""

PAGE_TEXT: list[datatypes.BaseText] = [
    datatypes.BaseText(
        id="text-28-2",
        text="FUENTES DE LUZ",
    ),
    datatypes.BaseText(
        id="text-28-14",
        text="TIPO DE CUERPO",
    ),
    datatypes.BaseText(
        id="text-28-15",
        text="CARACTERÍSTICAS",
    ),
    datatypes.BaseText(
        id="text-28-6",
        text="estrellas",
    ),
    datatypes.BaseText(
        id="text-28-0",
        text="Relee el artículo «La luz y la sombra».",
    ),
    datatypes.BaseText(
        id="text-28-1",
        text="Completa el cuadro con las palabras de la lista.",
    ),
    datatypes.BaseText(
        id="text-28-3",
        text="NATURAL",
    ),
    datatypes.BaseText(
        id="text-28-4",
        text="ARTIFICIAL",
    ),
    datatypes.BaseText(
        id="text-28-5",
        text="sol",
    ),
    datatypes.BaseText(
        id="text-28-8",
        text="linterna",
    ),
    datatypes.BaseText(
        id="text-28-7",
        text="vela",
    ),
    datatypes.BaseText(
        id="text-28-10",
        text="luciérnagas",
    ),
    datatypes.BaseText(
        id="text-28-11",
        text="rayos",
    ),
    datatypes.BaseText(
        id="text-28-12",
        text="lámpara eléctrica",
    ),
    datatypes.BaseText(
        id="text-28-13",
        text="Completa el cuadro que resume información sobre el tema.",
    ),
    datatypes.BaseText(
        id="text-28-19",
        text="vidrio esmerilado",
    ),
    datatypes.BaseText(
        id="text-28-18",
        text="Permiten el paso de la luz y se puede ver a través de ellos con nitidez.",
    ),
    datatypes.BaseText(
        id="text-28-17",
        text="opaco",
    ),
    datatypes.BaseText(
        id="text-28-16",
        text="EJEMPLOS",
    ),
    datatypes.BaseText(
        id="text-28-9",
        text="fuego",
    ),
]

ASSISTANT_RESPONSE = example_datatypes.SectioningResponseFormatExample(
    reasoning="",
    data=[
        task_datatypes.SectionData(
            section_id=1,
            section_type=datatypes.SectionType.activity_fill_in_a_table,
            id="text-28-3",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_sorting,
            id="text-28-4",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_sorting,
            id="text-28-5",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_sorting,
            id="text-28-8",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_sorting,
            id="text-28-7",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_sorting,
            id="text-28-10",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_sorting,
            id="text-28-11",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_sorting,
            id="text-28-12",
        ),
        task_datatypes.SectionData(
            section_id=1,
            section_type=datatypes.SectionType.activity_fill_in_a_table,
            id="text-28-13",
        ),
        task_datatypes.SectionData(
            section_id=1,
            section_type=datatypes.SectionType.activity_fill_in_a_table,
            id="text-28-19",
        ),
        task_datatypes.SectionData(
            section_id=1,
            section_type=datatypes.SectionType.activity_fill_in_a_table,
            id="text-28-18",
        ),
        task_datatypes.SectionData(
            section_id=1,
            section_type=datatypes.SectionType.activity_fill_in_a_table,
            id="text-28-17",
        ),
        task_datatypes.SectionData(
            section_id=1,
            section_type=datatypes.SectionType.activity_fill_in_a_table,
            id="text-28-16",
        ),
        task_datatypes.SectionData(
            section_id=0,
            section_type=datatypes.SectionType.activity_sorting,
            id="text-28-9",
        ),
    ],
)

CUADERNO_3_27_EXAMPLE: list[messages.Example] = [
    messages.Example(
        debug_name="cuaderno_3_27_user",
        role=datatypes.MessageRole.USER,
        content=[
            messages.TextContent(text=extraction_message_constants.PAGE_CONTEXT_PREFACE),
            messages.ImageContent(
                image_path="sectioning_examples/multiple_activities_2/cuaderno3_27.png"
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
        debug_name="cuaderno_3_27_assistant",
        role=datatypes.MessageRole.ASSISTANT,
        content=ASSISTANT_RESPONSE,
    ),
]
