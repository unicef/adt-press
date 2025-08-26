

from adt_press.llm.speech_generation import generate_speech_file
from adt_press.models.config import PromptConfig
from adt_press.models.speech import SpeechFile
from adt_press.utils.sync import gather_with_limit, run_async_task


def speech_files(run_output_dir_config: str, speech_prompt_config: PromptConfig, plate_translations: dict[str, dict[str, str]]) -> dict[str, dict[str, SpeechFile]]:
    async def generate_speech_files():
        tts = []
        for language, texts in plate_translations.items():
            for text_id, text in texts.items():
                tts.append(generate_speech_file(run_output_dir_config, speech_prompt_config, language, text_id, text))

        return await gather_with_limit(tts, speech_prompt_config.rate_limit)

    lang_to_tts = {lang: dict[str, SpeechFile]() for lang in plate_translations.keys()}
    files = run_async_task(generate_speech_files)
    for file in files:
        lang_to_tts[file.language_code][file.text_id] = file

    return lang_to_tts
