import json
from pydantic_core import to_jsonable_python
from accessible_digital_textbooks import datatypes
from accessible_digital_textbooks.async_tasks import extraction_message_constants, task_datatypes
from accessible_digital_textbooks.few_shot import example_datatypes, messages

"""
Reference text extracted from page.

31,text-31-0,es,Función de los bosques,section_heading,0,text_and_images,en
31,text-31-1,es,Fotosíntesis,image_label,0,text_and_images,en
31,text-31-2,es,Hábitat,image_label,0,text_and_images,en
31,text-31-3,es,Control de la erosión,image_label,0,text_and_images,en
31,text-31-4,es,Intercepción y redistribución de las precipitaciones,image_label,0,text_and_images,en
31,text-31-5,es,Almacenamiento de agua,image_label,0,text_and_images,en
31,text-31-6,es,Los bosques proporcionan un hábitat a una amplia variedad de plantas y animales y cumplen muchas otras funciones que afectan a los seres humanos.,section_text,1,text_only,en
31,text-31-7,es,"Junto con otras, estas grandes comunidades vegetales son responsables, por ejemplo, de la producción de oxígeno durante la fotosíntesis.",section_text,1,text_only,en
31,text-31-8,es,La fotosíntesis es el proceso químico mediante el cual hojas y tallos verdes usan la luz del sol y el dióxido de carbono para producir azúcares que proporcionan energía al árbol.,section_text,1,text_only,en
31,text-31-9,es,"Durante el proceso, el follaje de los árboles libera oxígeno, elemento necesario para la respiración.",section_text,1,text_only,en
31,text-31-10,es,"Los bosques también impiden la erosión, es decir, el desgaste del suelo producido por el viento y la lluvia.",section_text,2,text_only,en
31,text-31-11,es,"En parajes desnudos, con poca o ninguna vegetación, la lluvia puede arrastrar el suelo hacia ríos y arroyos, provocando corrimientos de tierra e inundaciones.",section_text,2,text_only,en
31,text-31-12,es,"Sin embargo, en zonas densamente arboladas las raíces de los árboles y de las plantas sujetan el suelo y frenan estos procesos.",section_text,2,text_only,en
31,text-31-13,es,"En áreas boscosas, la bóveda de hojas (la copa de los árboles) intercepta y redistribuye gradualmente el agua de la lluvia.",section_text,3,text_only,en
31,text-31-14,es,Una parte de la precipitación fluye entonces por la corteza de los troncos y el resto se escurre a través de las ramas y el follaje.,section_text,3,text_only,en
31,text-31-15,es,Esa distribución más lenta y poco uniforme de la lluvia contribuye a que el suelo no sea arrastrado de forma inmediata.,section_text,3,text_only,en
31,text-31-16,es,"De este modo, se reduce la posibilidad de anegamiento y erosión.",section_text,3,text_only,en
31,text-31-17,es,Los bosques también pueden aumentar la capacidad de la tierra para retener y almacenar reservas de agua.,section_text,4,text_only,en
31,text-31-18,es,La bóveda de hojas es especialmente eficiente para capturar agua procedente de la niebla (vapor de agua condensado).,section_text,4,text_only,en
31,text-31-19,es,El agua capturada en las copas de los árboles se distribuye luego en la 
31,text-31-20,es,"El agua almacenada en las raíces, los troncos, los tallos, el follaje y el suelo del terreno forestal permite a los bosques mantener un flujo constante de humedad en tiempos de sequías.",section_text,4,text_only,en
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
