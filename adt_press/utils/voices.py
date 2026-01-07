"""Voice mappings for TTS providers."""

import os
from functools import lru_cache
from typing import Any, Dict, cast

import yaml


@lru_cache(maxsize=1)
def load_voice_config() -> Dict[str, Any]:
    """Load voice configuration from YAML file (cached)."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "voices.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        result = yaml.safe_load(f)
        return cast(Dict[str, Any], result)


def get_provider_config(provider_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific provider.

    Args:
        provider_name: Name of the provider (e.g., "openai", "azure", "elevenlabs")

    Returns:
        Provider configuration dictionary

    Raises:
        ValueError: If provider not found in voices.yaml
    """
    config = load_voice_config()
    provider_config = config.get(provider_name)
    if provider_config is None:
        raise ValueError(f"Missing '{provider_name}' configuration in voices.yaml. Available providers: {list(config.keys())}")
    return cast(Dict[str, Any], provider_config)


def get_default_voice(provider_name: str) -> str:
    """
    Get the default voice for a provider.

    Args:
        provider_name: Name of the provider (e.g., "openai", "azure")

    Returns:
        Default voice name for the provider
    """
    provider_config = get_provider_config(provider_name)
    default_voice = provider_config.get("default")
    if default_voice is None:
        raise ValueError(f"Missing 'default' voice in {provider_name} configuration")
    return cast(str, default_voice)


def get_voice_map(provider_name: str) -> Dict[str, str]:
    """
    Get language-to-voice mapping for a provider.

    Args:
        provider_name: Name of the provider (e.g., "openai", "azure")

    Returns:
        Dictionary mapping language codes to voice names
    """
    provider_config = get_provider_config(provider_name)
    voices = provider_config.get("voices")
    if voices is None:
        return {}
    return cast(Dict[str, str], voices)


def get_voice_for_language(provider_name: str, language_code: str) -> str:
    """
    Get the appropriate voice for a language and provider.

    Args:
        provider_name: Name of the provider (e.g., "openai", "azure", "elevenlabs")
        language_code: ISO language code (e.g., "en", "es-uy", "fr-ca")

    Returns:
        Voice name for the provider
    """
    voice_map = get_voice_map(provider_name)

    # Normalize to lowercase
    normalized = language_code.lower()

    # Try exact match first (e.g., "es-uy")
    if normalized in voice_map:
        return voice_map[normalized]

    # Try base language (e.g., "es" from "es-uy")
    base_lang = normalized.split("-")[0]
    if base_lang in voice_map:
        return voice_map[base_lang]

    # Fall back to default voice
    return get_default_voice(provider_name)
