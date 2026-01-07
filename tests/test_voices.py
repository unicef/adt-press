"""Tests for voice utility functions."""

from unittest.mock import patch

import pytest

from adt_press.utils.voices import (
    get_default_voice,
    get_provider_config,
    get_voice_for_language,
    get_voice_map,
    load_voice_config,
)


class TestLoadVoiceConfig:
    """Test voice configuration loading."""

    def test_load_voice_config_success(self):
        """Test loading voice config from existing file."""
        config = load_voice_config()

        # Should have expected provider keys
        assert "openai" in config
        assert "azure" in config

        # Each provider should have default and voices
        assert "default" in config["openai"]
        assert "voices" in config["openai"]
        assert "default" in config["azure"]
        assert "voices" in config["azure"]

    def test_load_voice_config_cached(self):
        """Test that voice config is cached after first load."""
        # First call
        config1 = load_voice_config()

        # Second call should return same object (cached)
        config2 = load_voice_config()

        assert config1 is config2

    def test_load_voice_config_missing_file_raises(self):
        """Test that missing config file raises error."""
        # Mock the config path to a non-existent location
        with patch("adt_press.utils.voices.os.path.join", return_value="/nonexistent/path/voices.yaml"):
            # Clear cache
            load_voice_config.cache_clear()

            # Should raise FileNotFoundError
            with pytest.raises(FileNotFoundError):
                load_voice_config()

            # Clear cache again for other tests
            load_voice_config.cache_clear()


class TestGetProviderConfig:
    """Test provider configuration retrieval."""

    def test_get_provider_config_openai(self):
        """Test getting OpenAI provider config."""
        config = get_provider_config("openai")

        assert isinstance(config, dict)
        assert "default" in config
        assert "voices" in config

    def test_get_provider_config_azure(self):
        """Test getting Azure provider config."""
        config = get_provider_config("azure")

        assert isinstance(config, dict)
        assert "default" in config
        assert "voices" in config

    def test_get_provider_config_missing_raises(self):
        """Test that missing provider raises error."""
        with pytest.raises(ValueError, match="Missing 'nonexistent' configuration"):
            get_provider_config("nonexistent")


class TestGetVoiceMap:
    """Test voice map retrieval."""

    def test_get_voice_map_openai_returns_dict(self):
        """Test that get_voice_map returns a dictionary for OpenAI."""
        voice_map = get_voice_map("openai")

        assert isinstance(voice_map, dict)

    def test_get_voice_map_azure_returns_dict(self):
        """Test that get_voice_map returns a dictionary for Azure."""
        voice_map = get_voice_map("azure")

        assert isinstance(voice_map, dict)

    def test_get_voice_map_contains_expected_languages(self):
        """Test that voice map contains expected language mappings."""
        voice_map = get_voice_map("azure")

        # Should have some common languages
        assert len(voice_map) > 0

        # Check that values are strings (voice names)
        for voice_name in voice_map.values():
            assert isinstance(voice_name, str)
            assert len(voice_name) > 0


class TestGetDefaultVoice:
    """Test default voice retrieval."""

    def test_get_default_voice_openai(self):
        """Test getting default OpenAI voice."""
        default_voice = get_default_voice("openai")
        assert isinstance(default_voice, str)
        assert len(default_voice) > 0

    def test_get_default_voice_azure(self):
        """Test getting default Azure voice."""
        default_voice = get_default_voice("azure")
        assert isinstance(default_voice, str)
        assert "Neural" in default_voice

    def test_get_default_voice_missing_provider(self):
        """Test that missing provider raises error."""
        with pytest.raises(ValueError, match="Missing 'nonexistent' configuration"):
            get_default_voice("nonexistent")


class TestGetVoiceForLanguage:
    """Test voice selection by language code."""

    def test_get_voice_for_language_exact_match(self):
        """Test exact language code match."""
        # Mock voice map
        mock_map = {
            "en": "en-US-JennyNeural",
            "es": "es-ES-ElviraNeural",
            "fr": "fr-FR-DeniseNeural",
        }

        with patch("adt_press.utils.voices.get_voice_map", return_value=mock_map):
            with patch("adt_press.utils.voices.get_default_voice", return_value="default"):
                assert get_voice_for_language("azure", "en") == "en-US-JennyNeural"
                assert get_voice_for_language("azure", "es") == "es-ES-ElviraNeural"
                assert get_voice_for_language("azure", "fr") == "fr-FR-DeniseNeural"

    def test_get_voice_for_language_case_insensitive(self):
        """Test that language code matching is case-insensitive."""
        mock_map = {
            "en": "en-US-JennyNeural",
        }

        with patch("adt_press.utils.voices.get_voice_map", return_value=mock_map):
            with patch("adt_press.utils.voices.get_default_voice", return_value="default"):
                assert get_voice_for_language("azure", "EN") == "en-US-JennyNeural"
                assert get_voice_for_language("azure", "En") == "en-US-JennyNeural"

    def test_get_voice_for_language_base_language_fallback(self):
        """Test fallback to base language when regional variant not found."""
        mock_map = {
            "es": "es-ES-ElviraNeural",
            "fr": "fr-FR-DeniseNeural",
        }

        with patch("adt_press.utils.voices.get_voice_map", return_value=mock_map):
            with patch("adt_press.utils.voices.get_default_voice", return_value="default"):
                # es-uy should fall back to es
                assert get_voice_for_language("azure", "es-uy") == "es-ES-ElviraNeural"

                # fr-ca should fall back to fr
                assert get_voice_for_language("azure", "fr-ca") == "fr-FR-DeniseNeural"

    def test_get_voice_for_language_no_match_returns_default(self):
        """Test that default is returned when no match is found."""
        mock_map = {
            "en": "en-US-JennyNeural",
            "es": "es-ES-ElviraNeural",
        }

        with patch("adt_press.utils.voices.get_voice_map", return_value=mock_map):
            with patch("adt_press.utils.voices.get_default_voice", return_value="default-voice"):
                assert get_voice_for_language("azure", "xx") == "default-voice"
                assert get_voice_for_language("azure", "zz-ZZ") == "default-voice"

    def test_get_voice_for_language_regional_exact_match_priority(self):
        """Test that exact regional match takes priority over base language."""
        mock_map = {
            "es": "es-ES-ElviraNeural",
            "es-mx": "es-MX-DaliaNeural",
        }

        with patch("adt_press.utils.voices.get_voice_map", return_value=mock_map):
            with patch("adt_press.utils.voices.get_default_voice", return_value="default"):
                # Exact match for es-mx
                assert get_voice_for_language("azure", "es-mx") == "es-MX-DaliaNeural"

                # Fallback to base es for es-ar
                assert get_voice_for_language("azure", "es-ar") == "es-ES-ElviraNeural"

    def test_get_voice_for_language_with_real_config(self):
        """Test with real voice configuration (integration test)."""
        # This tests the actual config file
        voice = get_voice_for_language("azure", "en")

        # Should get a valid English voice
        assert voice is not None
        assert isinstance(voice, str)
        assert len(voice) > 0

    def test_get_voice_for_language_openai(self):
        """Test OpenAI voice selection."""
        voice = get_voice_for_language("openai", "en")
        assert voice is not None
        assert isinstance(voice, str)

    def test_get_voice_for_language_empty_string(self):
        """Test handling of empty language code."""
        mock_map = {
            "en": "en-US-JennyNeural",
        }

        with patch("adt_press.utils.voices.get_voice_map", return_value=mock_map):
            with patch("adt_press.utils.voices.get_default_voice", return_value="default"):
                result = get_voice_for_language("azure", "")
                assert result == "default"
