import os

import litellm
from pydub import AudioSegment

from adt_press.models.config import SpeechPromptConfig
from adt_press.models.speech import SpeechFile
from adt_press.utils.encoding import strip_emojis
from adt_press.utils.html import render_template_to_string
from adt_press.utils.languages import Language
from adt_press.utils.voices import get_azure_voice, get_openai_voices


def resolve_voice(model: str, requested_voice: str, language_code: str) -> str:
    """
    Resolve the appropriate voice based on model and language.

    Args:
        model: TTS model (e.g., "tts-1", "azure/speech/azure-tts")
        requested_voice: Voice from config ("auto" or specific voice name)
        language_code: ISO language code (e.g., "si", "en", "ta")

    Returns:
        Valid voice name for the model
    """
    is_azure = model.startswith("azure/")

    # Auto mode - choose best voice for language
    if requested_voice == "auto":
        if is_azure:
            voice = get_azure_voice(language_code)
            if voice:
                return voice

            # Final fallback to English
            return "en-US-JennyNeural"
        else:
            return "alloy"  # OpenAI default

    # Validate requested voice matches model
    if is_azure:
        # Check if it's an Azure voice format (xx-XX-NameNeural)
        if "-" in requested_voice and "Neural" in requested_voice:
            return requested_voice

        # Requested non-Azure voice with Azure model - fall back
        voice = get_azure_voice(language_code)
        return voice if voice else "en-US-JennyNeural"
    else:
        # OpenAI model
        openai_voices = get_openai_voices()
        if requested_voice in openai_voices:
            return requested_voice

        # Requested Azure voice with OpenAI model - fall back to default
        return "alloy"


async def generate_speech_file(
    run_output_dir: str,
    config: SpeechPromptConfig,
    language: Language,
    text_id: str,
    text: str,
) -> SpeechFile:
    """
    Generate a speech file from text using TTS.

    Args:
        run_output_dir: Output directory for audio files
        config: Speech generation configuration
        language: Target language for speech
        text_id: Unique identifier for the text
        text: Text content to convert to speech

    Returns:
        SpeechFile metadata object

    Raises:
        FileNotFoundError: If TTS output file is not created
        ValueError: If TTS output file is empty or invalid
    """
    language_code = language.code

    sanitized_text = strip_emojis(text)
    if not sanitized_text.strip():
        sanitized_text = text

    context = dict(
        language_code=language_code,
        language=language.name,
        text=sanitized_text,
        examples=config.examples,
    )

    # Render prompt template for TTS instructions
    prompt = render_template_to_string(config.template_path, context)

    # Get active provider config
    model, voice = config.get_active_config()

    # Resolve the voice based on language
    resolved_voice = resolve_voice(model, voice, language_code)

    speech_id = f"{text_id}_{language_code}"
    speech_dir = os.path.join(run_output_dir, "audio", language_code)
    os.makedirs(speech_dir, exist_ok=True)

    raw_speech_path = os.path.join(speech_dir, f"{speech_id}_raw.mp3")
    speech_path = os.path.join(speech_dir, f"{speech_id}.{config.format}")

    # Build kwargs - Azure Speech doesn't support instructions parameter
    speech_kwargs = {
        "model": model,
        "voice": resolved_voice,
        "input": sanitized_text,
        "response_format": "mp3",
    }

    # Only add instructions for OpenAI-compatible models (not Azure Speech)
    if not model.startswith("azure/"):
        speech_kwargs["instructions"] = prompt

    # Generate speech via TTS API
    response = await litellm.aspeech(**speech_kwargs)

    # Write the audio response to file
    # For Azure, this returns HttpxBinaryResponseContent which needs special handling
    if hasattr(response, "content"):
        # Response has content attribute (likely bytes)
        with open(raw_speech_path, "wb") as f:
            f.write(response.content)
    elif hasattr(response, "read"):
        # Response is a file-like object
        with open(raw_speech_path, "wb") as f:
            f.write(response.read())
    else:
        # Use litellm's write_to_file method as fallback
        response.write_to_file(raw_speech_path)

    # Verify file was written successfully
    if not os.path.exists(raw_speech_path):
        raise FileNotFoundError(f"TTS output file not created: {raw_speech_path}")

    file_size = os.path.getsize(raw_speech_path)
    if file_size == 0:
        raise ValueError(f"TTS output file is empty: {raw_speech_path}")

    # Transcode to quality specified in config
    raw = AudioSegment.from_mp3(raw_speech_path)
    raw.set_frame_rate(config.sample_rate)
    raw.export(speech_path, bitrate=config.bit_rate, format=config.format, parameters=["-ac", "1"])

    speech_relative_path = os.path.join("audio", language_code, f"{speech_id}.{config.format}")
    return SpeechFile(
        speech_id=speech_id,
        speech_path=speech_relative_path,
        language_code=language_code,
        text_id=text_id,
    )
