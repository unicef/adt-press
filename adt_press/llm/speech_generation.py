import os

import litellm
from pydub import AudioSegment

from adt_press.models.config import SpeechPromptConfig
from adt_press.models.speech import SpeechFile
from adt_press.utils.encoding import strip_emojis
from adt_press.utils.html import render_template_to_string
from adt_press.utils.languages import Language


async def generate_speech_file(run_output_dir: str, config: SpeechPromptConfig, language: Language, text_id: str, text: str) -> SpeechFile:
    sanitized_text = strip_emojis(text)
    if not sanitized_text.strip():
        sanitized_text = text

    context = dict(
        language_code=language.name,
        language=language,
        text=sanitized_text,
        examples=config.examples,
    )

    # since we are calling the speech endpoint, not completion, we don't use banks but render straight to text
    prompt = render_template_to_string(config.template_path, context)

    speech_id = f"{text_id}_{language_code}"
    speech_dir = os.path.join(run_output_dir, "audio", language_code)
    os.makedirs(speech_dir, exist_ok=True)

    raw_speech_path = os.path.join(speech_dir, f"{speech_id}_raw.mp3")
    speech_path = os.path.join(speech_dir, f"{speech_id}.{config.format}")

    # feed the sanitized string to TTS to avoid emoji artifacts in playback
    response = await litellm.aspeech(
        model=config.model,
        voice=config.voice,
        input=sanitized_text,
        instructions=prompt,
        response_format="mp3",
    )
    response.write_to_file(raw_speech_path)

    # transcode to quality specified in our config
    raw = AudioSegment.from_mp3(raw_speech_path)
    raw.set_frame_rate(config.sample_rate)
    raw.export(speech_path, bitrate=config.bit_rate, format=config.format, parameters=["-ac", "1"])

    speech_relative_path = os.path.join("audio", language_code, f"{speech_id}.{config.format}")
    return SpeechFile(speech_id=speech_id, speech_path=speech_relative_path, language_code=language_code, text_id=text_id)
