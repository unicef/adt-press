import os
import shutil

import litellm
from pydub import AudioSegment

from adt_press.models.config import SpeechPromptConfig
from adt_press.models.ids import SpeechID, TextID
from adt_press.models.speech import SpeechFile
from adt_press.utils.encoding import strip_emojis
from adt_press.utils.html import render_template_to_string
from adt_press.utils.languages import Language
from adt_press.utils.string import is_speakable_text


def resolve_voice(provider: str, language_code: str, voice_maps: dict[str, dict[str, str]]) -> str:
    """
    Resolve the appropriate voice based on provider and language using cached voice maps.

    Args:
        provider: TTS provider name (e.g., "openai", "azure", "elevenlabs")
        language_code: ISO language code (e.g., "si", "en", "ta")
        voice_maps: Cached voice configuration maps from voices.yaml

    Returns:
        Valid voice name for the provider

    Raises:
        ValueError: If provider not found or missing 'default' voice
    """
    if provider not in voice_maps:
        raise ValueError(f"Missing '{provider}' configuration in voices file. Available providers: {list(voice_maps.keys())}")

    provider_config = voice_maps[provider]

    # Normalize to lowercase
    normalized = language_code.lower()

    # Try exact match first (e.g., "es-uy")
    if normalized in provider_config:
        return provider_config[normalized]

    # Try base language (e.g., "es" from "es-uy")
    base_lang = normalized.split("-")[0]
    if base_lang in provider_config:
        return provider_config[base_lang]

    # Fall back to default voice
    default_voice = provider_config.get("default")
    if default_voice is None:
        raise ValueError(f"Missing 'default' voice in {provider} configuration")
    return default_voice


async def generate_speech_file(
    run_output_dir: str,
    config: SpeechPromptConfig,
    voice_maps: dict[str, dict[str, str]],  # Add cached voice maps parameter
    language: Language,
    text_id: TextID,
    text: str,
) -> SpeechFile:
    """
    Generate a speech file from text using TTS.

    Args:
        run_output_dir: Output directory for audio files
        config: Speech generation configuration
        voice_maps: Cached voice configuration maps (from Hamilton node)
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

    # Sanitize and validate text
    sanitized_text = strip_emojis(text)
    if not sanitized_text.strip():
        sanitized_text = text

    if not sanitized_text or not sanitized_text.strip():
        raise ValueError(
            f"Empty or whitespace-only text for TTS generation: text_id={text_id}, "
            f"language={language_code}, original_text='{text[:100] if text else 'EMPTY'}'"
        )

    # Setup common paths and metadata
    speech_id = SpeechID(f"{text_id}_{language_code}")
    speech_dir = os.path.join(run_output_dir, "audio", language_code)
    os.makedirs(speech_dir, exist_ok=True)
    speech_path = os.path.join(speech_dir, f"{speech_id}.{config.format}")
    speech_relative_path = os.path.join("audio", language_code, f"{speech_id}.{config.format}")

    # Get provider config and resolve voice using cached voice maps
    model = config.get_active_config(language_code)
    resolved_provider = config.get_provider_for_language(language_code)
    resolved_voice = resolve_voice(resolved_provider, language_code, voice_maps)  # Pass cached maps

    # Handle non-speakable text (e.g., punctuation-only like "—")
    if not is_speakable_text(sanitized_text):
        # Copy prebuilt empty audio file
        empty_template = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "audio", "empty.mp3")
        if not os.path.exists(empty_template):
            raise FileNotFoundError(f"Empty audio template not found: {empty_template}")

        shutil.copy2(empty_template, speech_path)

        return SpeechFile(
            speech_id=speech_id,
            text_id=text_id,
            speech_path=speech_relative_path,
            language_code=language_code,
            provider=resolved_provider,
            voice=resolved_voice,
            model=model,
        )

    # Render prompt template for TTS instructions
    context = dict(
        language_code=language_code,
        language=language.name,
        text=sanitized_text,
        examples=config.examples,
    )
    prompt = render_template_to_string(config.template_path, context)

    # Generate speech via TTS
    raw_speech_path = os.path.join(speech_dir, f"{speech_id}_raw.{config.format}")

    # Build kwargs - Azure Speech doesn't support instructions parameter
    speech_kwargs = {
        "model": model,
        "voice": resolved_voice,
        "input": sanitized_text,
        "response_format": config.format,
    }

    # Only add instructions for OpenAI-compatible models (not Azure Speech)
    if not model.startswith("azure/"):
        speech_kwargs["instructions"] = prompt

    response = await litellm.aspeech(**speech_kwargs)

    # Write the audio response to file
    try:
        if hasattr(response, "write_to_file"):
            # Preferred litellm method
            response.write_to_file(raw_speech_path)
        else:
            # Fallback: treat as bytes-like content
            content = response.content if hasattr(response, "content") else response.read()
            if hasattr(content, "__await__"):
                content = await content
            with open(raw_speech_path, "wb") as f:
                f.write(content)
    except Exception as e:
        raise ValueError(f"Failed to write TTS response to file: {e}\nResponse type: {type(response)}, Attributes: {dir(response)}") from e

    # Verify file was written successfully
    if not os.path.exists(raw_speech_path) or os.path.getsize(raw_speech_path) == 0:
        raise FileNotFoundError(f"TTS output file not created or empty: {raw_speech_path}")

    # Transcode to quality specified in config
    raw = AudioSegment.from_file(raw_speech_path, format=config.format)
    raw.set_frame_rate(config.sample_rate)
    raw.export(speech_path, bitrate=config.bit_rate, format=config.format, parameters=["-ac", "1"])

    return SpeechFile(
        speech_id=speech_id,
        text_id=text_id,
        speech_path=speech_relative_path,
        language_code=language_code,
        provider=resolved_provider,
        voice=resolved_voice,
        model=model,
    )
