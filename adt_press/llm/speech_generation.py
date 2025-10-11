import os

import litellm

from adt_press.models.config import PromptConfig
from adt_press.models.speech import SpeechFile


async def generate_speech_file(
    run_output_dir: str,
    config: PromptConfig,
    language_code: str,
    text_id: str,
    text: str,
) -> SpeechFile:
    speech_id = f"{text_id}_{language_code}"
    speech_dir = os.path.join(run_output_dir, "audio", language_code)
    os.makedirs(speech_dir, exist_ok=True)

    speech_path = os.path.join(speech_dir, f"{speech_id}.mp3")

    # Standard OpenAI TTS models (tts-1, tts-1-hd)
    # don't support instructions parameter.
    # TODO: Add instruction support when audio models support it
    response = await litellm.aspeech(
        model=config.model,
        voice="alloy",
        input=text,
        response_format="mp3",
    )
    response.write_to_file(speech_path)

    speech_relative_path = os.path.join(
        "audio", language_code, f"{speech_id}.mp3"
    )
    return SpeechFile(
        speech_id=speech_id,
        speech_path=speech_relative_path,
        language_code=language_code,
        text_id=text_id,
    )
