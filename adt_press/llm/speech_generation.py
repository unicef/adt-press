import os

import litellm
from pydub import AudioSegment

from adt_press.models.config import SpeechPromptConfig
from adt_press.models.speech import SpeechFile
from adt_press.utils.encoding import strip_emojis
from adt_press.utils.html import render_template_to_string
from adt_press.utils.languages import Language
from adt_press.utils.string import is_speakable_text
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

    # Validate text before attempting TTS
    if not sanitized_text or not sanitized_text.strip():
        raise ValueError(
            f"Empty or whitespace-only text for TTS generation: text_id={text_id}, "
            f"language={language_code}, original_text='{text[:100] if text else 'EMPTY'}'"
        )

    # Skip texts that aren't suitable for TTS (e.g., punctuation-only like "—")
    # Azure TTS often returns empty responses for such content
    if not is_speakable_text(sanitized_text):
        # Return a minimal silent audio file instead of failing
        speech_dir = os.path.join(run_output_dir, "audio", language_code)
        os.makedirs(speech_dir, exist_ok=True)
        speech_id = f"{text_id}_{language_code}"
        speech_path = os.path.join(speech_dir, f"{speech_id}.{config.format}")

        # Create silent audio segment (50ms)
        silent_audio = AudioSegment.silent(duration=50)
        silent_audio.export(
            speech_path,
            format=config.format,
            bitrate=config.bit_rate,
            parameters=["-ar", str(config.sample_rate)],
        )

        # Get provider/voice for metadata (even though we didn't use TTS)
        model, voice = config.get_active_config()

        return SpeechFile(
            text_id=text_id,
            speech_id=speech_id,
            speech_path=speech_path,
            language_code=language_code,
            provider=config.provider,
            voice=voice,
            model=model,
        )

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

    response = await litellm.aspeech(**speech_kwargs)

    # Write the audio response to file
    # Different response types require different handling
    try:
        if hasattr(response, "write_to_file"):
            # Use litellm's write_to_file method (most reliable, handles all types)
            response.write_to_file(raw_speech_path)
        elif hasattr(response, "read"):
            # Response is a file-like object
            with open(raw_speech_path, "wb") as f:
                content = response.read()
                f.write(content)
        elif hasattr(response, "content"):
            # Response has content attribute (likely bytes)
            content = response.content
            # For httpx responses, content might be a coroutine
            if hasattr(content, "__await__"):
                content = await content
            with open(raw_speech_path, "wb") as f:
                f.write(content)
        elif hasattr(response, "iter_bytes"):
            # Streaming response
            with open(raw_speech_path, "wb") as f:
                async for chunk in response.iter_bytes():
                    f.write(chunk)
        else:
            raise ValueError(f"Unknown response type: {type(response)}, attributes: {dir(response)}")
    except Exception as e:
        raise ValueError(f"Failed to write TTS response to file: {e}, response type: {type(response)}")

    # Verify file was written successfully
    if not os.path.exists(raw_speech_path):
        raise FileNotFoundError(f"TTS output file not created: {raw_speech_path}")

    file_size = os.path.getsize(raw_speech_path)
    if file_size == 0:
        raise ValueError(
            f"TTS output file is empty: {raw_speech_path}\n"
            f"Text ID: {text_id}, Language: {language_code}, Model: {model}, Voice: {resolved_voice}\n"
            f"Text length: {len(sanitized_text)}, Preview: '{sanitized_text[:200]}'"
        )

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
        provider=config.provider,
        voice=resolved_voice,
        model=model,
    )
