import os
import instructor
from banks import Prompt
from litellm import acompletion
import litellm
from pydantic import BaseModel

from adt_press.models.config import PromptConfig
from adt_press.models.text import OutputText
from adt_press.models.speech import SpeechFile
from adt_press.utils import config
from adt_press.utils.file import cached_read_text_file
from adt_press.utils.html import render_template_to_string
from adt_press.utils.languages import LANGUAGE_MAP


async def generate_speech_file(run_output_dir: str, config: PromptConfig, language_code: str, text_id: str, text: str) -> SpeechFile:

    language = LANGUAGE_MAP[language_code]

    context = dict(
        language_code=language_code,
        language=language,
        text=text,
        examples=config.examples,
    )

    # since we are calling the speech endpoint, not completion, we don't use banks but render straight to text
    prompt = render_template_to_string(config.template_path, context)

    speech_id = f"tts_{language_code}_{text_id}"
    speech_dir = os.path.join(run_output_dir, "audio", language_code)
    os.makedirs(speech_dir, exist_ok=True)

    

    speech_path = os.path.join(speech_dir, f"{speech_id}.mp3")

    response = await litellm.aspeech(
            model=config.model,
            voice="alloy",
            input=text,
            instructions=prompt,
            response_format="mp3",
    )
    response.write_to_file(speech_path)

    speech_relative_path = os.path.join("audio", language_code, f"{speech_id}.mp3")
    return SpeechFile(speech_id=speech_id, speech_upath=speech_relative_path, language_code=language_code, text_id=text_id)
