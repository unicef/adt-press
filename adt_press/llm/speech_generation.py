import os

import litellm
import structlog
from pydub import AudioSegment

from adt_press.models.config import SpeechPromptConfig
from adt_press.models.speech import SpeechFile
from adt_press.utils.encoding import strip_emojis
from adt_press.utils.html import render_template_to_string
from adt_press.utils.languages import Language

log = structlog.get_logger(__name__)

# Voice catalogs
OPENAI_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

AZURE_VOICE_MAP = {
    "en": "en-US-JennyNeural",
    "es": "es-ES-ElviraNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "it": "it-IT-ElsaNeural",
    "pt": "pt-BR-FranciscaNeural",
    "si": "si-LK-ThiliniNeural",
    "ta": "ta-IN-PallaviNeural",
    "ar": "ar-SA-ZariyahNeural",
    "hi": "hi-IN-SwaraNeural",
    "bn": "bn-IN-TanishaaNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
}


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
            voice = AZURE_VOICE_MAP.get(language_code, "en-US-JennyNeural")
            if language_code not in AZURE_VOICE_MAP:
                log.warning(
                    "azure_voice_fallback",
                    language_code=language_code,
                    fallback_voice=voice,
                    message=f"No Azure voice mapping for language '{language_code}', using default",
                )
            return voice
        else:
            return "alloy"  # OpenAI default

    # Validate requested voice matches model
    if is_azure:
        # Check if it's an Azure voice format (xx-XX-NameNeural)
        if "-" in requested_voice and "Neural" in requested_voice:
            return requested_voice
        # Requested non-Azure voice with Azure model - fall back
        fallback = AZURE_VOICE_MAP.get(language_code, "en-US-JennyNeural")
        log.warning(
            "voice_provider_mismatch",
            requested_voice=requested_voice,
            model=model,
            fallback_voice=fallback,
            message=f"Voice '{requested_voice}' not compatible with Azure, using {fallback}",
        )
        return fallback
    else:
        # OpenAI model
        if requested_voice in OPENAI_VOICES:
            return requested_voice
        # Requested Azure voice with OpenAI model - fall back
        log.warning(
            "voice_provider_mismatch",
            requested_voice=requested_voice,
            model=model,
            fallback_voice="alloy",
            message=f"Voice '{requested_voice}' not compatible with OpenAI TTS, using 'alloy'",
        )
        return "alloy"


async def generate_speech_file(
    run_output_dir: str,
    config: SpeechPromptConfig,
    language: Language,
    text_id: str,
    text: str,
) -> SpeechFile:
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

    # since we are calling the speech endpoint, not completion, we don't use banks but render straight to text
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

    # feed the sanitized string to TTS to avoid emoji artifacts in playback
    response = await litellm.aspeech(**speech_kwargs)
    response.write_to_file(raw_speech_path)

    # transcode to quality specified in our config
    raw = AudioSegment.from_mp3(raw_speech_path)
    raw.set_frame_rate(config.sample_rate)
    raw.export(speech_path, bitrate=config.bit_rate, format=config.format, parameters=["-ac", "1"])

    speech_relative_path = os.path.join("audio", language_code, f"{speech_id}.{config.format}")
    return SpeechFile(speech_id=speech_id, speech_path=speech_relative_path, language_code=language_code, text_id=text_id)
