from banks import Prompt

from adt_press.llm import get_instructor_client
from adt_press.models.config import PromptConfig
from adt_press.models.section import GlossaryItem
from adt_press.utils.encoding import CleanTextBaseModel
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.languages import Language


class TranslationResponse(CleanTextBaseModel):
    reasoning: str
    word: str
    variants: list[str]
    definition: str


async def get_glossary_translation(
    config: PromptConfig,
    base_language: Language,
    target_language: Language,
    glossary_item: GlossaryItem,
) -> GlossaryItem:
    context = dict(
        base_language=base_language.name,
        target_language=target_language.name,
        glossary_item=glossary_item,
        examples=config.examples,
    )

    prompt = Prompt(cached_read_text_file(config.template_path))
    client = get_instructor_client()
    response: TranslationResponse = await client.chat.completions.create(
        model=config.model,
        response_model=TranslationResponse,
        messages=[m.model_dump(exclude_none=True) for m in prompt.chat_messages(context)],
        max_retries=config.max_retries,
        timeout=config.timeout,
    )

    return GlossaryItem(word=response.word, definition=response.definition, variations=response.variants, emojis=glossary_item.emojis)
