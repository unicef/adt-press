"""Voice mappings for TTS providers."""

import os
from functools import lru_cache
from typing import Dict, List, Optional

import structlog
import yaml

log = structlog.get_logger(__name__)


@lru_cache(maxsize=1)
def load_voice_config() -> Dict:
    """Load voice configuration from YAML file (cached)."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "voices.yaml")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        log.warning("voices_config_not_found", path=config_path, message="Using default voice mappings")
        # Fallback to minimal defaults
        return {
            "openai_voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
            "azure_voices": {
                "en": "en-US-JennyNeural",
                "es": "es-ES-ElviraNeural",
                "fr": "fr-FR-DeniseNeural",
            },
        }


def get_openai_voices() -> List[str]:
    """Get list of available OpenAI voices."""
    config = load_voice_config()
    return config.get("openai_voices", [])


def get_azure_voice_map() -> Dict[str, str]:
    """Get Azure voice mapping dictionary."""
    config = load_voice_config()
    return config.get("azure_voices", {})


def get_azure_voice(language_code: str) -> Optional[str]:
    """
    Get Azure voice for language code with fallback logic.

    Args:
        language_code: ISO language code (e.g., "es-uy", "en", "fr-ca")

    Returns:
        Azure voice name or None if no match found
    """
    voice_map = get_azure_voice_map()

    # Normalize to lowercase
    normalized = language_code.lower()

    # Try exact match first
    if normalized in voice_map:
        return voice_map[normalized]

    # Try base language (e.g., "es" from "es-uy")
    base_lang = normalized.split("-")[0]
    if base_lang in voice_map:
        return voice_map[base_lang]

    return None
