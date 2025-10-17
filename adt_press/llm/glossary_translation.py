import instructor
from banks import Prompt
from litellm import acompletion

from adt_press.models.config import PromptConfig
from adt_press.models.section import GlossaryItem
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.languages import LANGUAGE_MAP


class TranslationResponse(CleanTextBaseModel):
    reasoning: str
    word: str
    variants: list[str]
    definition: str


async def get_glossary_translation(
    config: PromptConfig,
    base_language_code: str,
    target_language_code: str,
    glossary_item: GlossaryItem,
) -> GlossaryItem:
    base_language = LANGUAGE_MAP[base_language_code]
    target_language = LANGUAGE_MAP[target_language_code]

    context = dict(
        base_language=base_language,
        target_language=target_language,
        glossary_item=glossary_item,
        examples=config.examples,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = instructor.from_litellm(acompletion)
    response: TranslationResponse = await client.chat.completions.create(
        model=config.model,
        response_model=TranslationResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
    )

    return GlossaryItem(word=response.word, definition=response.definition, variations=response.variants, emojis=glossary_item.emojis)
