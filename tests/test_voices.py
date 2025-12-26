"""Tests for voice utility functions."""

from unittest.mock import patch

from adt_press.utils.voices import (
    get_azure_voice,
    get_azure_voice_map,
    get_openai_voices,
    load_voice_config,
)


class TestLoadVoiceConfig:
    """Test voice configuration loading."""

    def test_load_voice_config_success(self):
        """Test loading voice config from existing file."""
        config = load_voice_config()

        # Should have expected keys
        assert "openai_voices" in config
        assert "azure_voices" in config

        # OpenAI voices should be a list
        assert isinstance(config["openai_voices"], list)

        # Azure voices should be a dict
        assert isinstance(config["azure_voices"], dict)

    def test_load_voice_config_cached(self):
        """Test that voice config is cached after first load."""
        # First call
        config1 = load_voice_config()

        # Second call should return same object (cached)
        config2 = load_voice_config()

        assert config1 is config2

    def test_load_voice_config_missing_file_fallback(self):
        """Test fallback when config file is missing."""
        # Mock the config path to a non-existent location
        with patch("adt_press.utils.voices.os.path.join", return_value="/nonexistent/path/voices.yaml"):
            # Clear cache
            load_voice_config.cache_clear()

            config = load_voice_config()

            # Should return fallback config
            assert "openai_voices" in config
            assert "azure_voices" in config
            assert "alloy" in config["openai_voices"]
            assert "en" in config["azure_voices"]

            # Clear cache again for other tests
            load_voice_config.cache_clear()


class TestGetOpenAIVoices:
    """Test OpenAI voice retrieval."""

    def test_get_openai_voices_returns_list(self):
        """Test that get_openai_voices returns a list of voices."""
        voices = get_openai_voices()

        assert isinstance(voices, list)
        assert len(voices) > 0

    def test_get_openai_voices_contains_expected_voices(self):
        """Test that OpenAI voices contain expected voice names."""
        voices = get_openai_voices()

        # Standard OpenAI voices
        expected_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

        # All expected voices should be present
        for voice in expected_voices:
            assert voice in voices

    def test_get_openai_voices_with_missing_key(self):
        """Test handling when openai_voices key is missing."""
        with patch("adt_press.utils.voices.load_voice_config", return_value={}):
            voices = get_openai_voices()
            assert voices == []


class TestGetAzureVoiceMap:
    """Test Azure voice map retrieval."""

    def test_get_azure_voice_map_returns_dict(self):
        """Test that get_azure_voice_map returns a dictionary."""
        voice_map = get_azure_voice_map()

        assert isinstance(voice_map, dict)

    def test_get_azure_voice_map_contains_expected_languages(self):
        """Test that Azure voice map contains expected language mappings."""
        voice_map = get_azure_voice_map()

        # Should have some common languages
        assert len(voice_map) > 0

        # Check that values are strings (voice names)
        for voice_name in voice_map.values():
            assert isinstance(voice_name, str)
            assert "Neural" in voice_name or voice_name != ""

    def test_get_azure_voice_map_with_missing_key(self):
        """Test handling when azure_voices key is missing."""
        with patch("adt_press.utils.voices.load_voice_config", return_value={}):
            voice_map = get_azure_voice_map()
            assert voice_map == {}


class TestGetAzureVoice:
    """Test Azure voice selection by language code."""

    def test_get_azure_voice_exact_match(self):
        """Test exact language code match."""
        # Mock voice map
        mock_map = {
            "en": "en-US-JennyNeural",
            "es": "es-ES-ElviraNeural",
            "fr": "fr-FR-DeniseNeural",
        }

        with patch("adt_press.utils.voices.get_azure_voice_map", return_value=mock_map):
            assert get_azure_voice("en") == "en-US-JennyNeural"
            assert get_azure_voice("es") == "es-ES-ElviraNeural"
            assert get_azure_voice("fr") == "fr-FR-DeniseNeural"

    def test_get_azure_voice_case_insensitive(self):
        """Test that language code matching is case-insensitive."""
        mock_map = {
            "en": "en-US-JennyNeural",
        }

        with patch("adt_press.utils.voices.get_azure_voice_map", return_value=mock_map):
            assert get_azure_voice("EN") == "en-US-JennyNeural"
            assert get_azure_voice("En") == "en-US-JennyNeural"

    def test_get_azure_voice_base_language_fallback(self):
        """Test fallback to base language when regional variant not found."""
        mock_map = {
            "es": "es-ES-ElviraNeural",
            "fr": "fr-FR-DeniseNeural",
        }

        with patch("adt_press.utils.voices.get_azure_voice_map", return_value=mock_map):
            # es-uy should fall back to es
            assert get_azure_voice("es-uy") == "es-ES-ElviraNeural"

            # fr-ca should fall back to fr
            assert get_azure_voice("fr-ca") == "fr-FR-DeniseNeural"

    def test_get_azure_voice_no_match_returns_none(self):
        """Test that None is returned when no match is found."""
        mock_map = {
            "en": "en-US-JennyNeural",
            "es": "es-ES-ElviraNeural",
        }

        with patch("adt_press.utils.voices.get_azure_voice_map", return_value=mock_map):
            assert get_azure_voice("xx") is None
            assert get_azure_voice("zz-ZZ") is None

    def test_get_azure_voice_regional_exact_match_priority(self):
        """Test that exact regional match takes priority over base language."""
        mock_map = {
            "es": "es-ES-ElviraNeural",
            "es-mx": "es-MX-DaliaNeural",
        }

        with patch("adt_press.utils.voices.get_azure_voice_map", return_value=mock_map):
            # Exact match for es-mx
            assert get_azure_voice("es-mx") == "es-MX-DaliaNeural"

            # Fallback to base es for es-ar
            assert get_azure_voice("es-ar") == "es-ES-ElviraNeural"

    def test_get_azure_voice_with_real_config(self):
        """Test with real voice configuration (integration test)."""
        # This tests the actual config file
        voice = get_azure_voice("en")

        # Should get a valid English voice
        assert voice is not None
        assert isinstance(voice, str)
        assert "Neural" in voice or voice.endswith("Neural")

    def test_get_azure_voice_sinhala(self):
        """Test Sinhala language voice selection."""
        voice_map = get_azure_voice_map()

        if "si" in voice_map:
            voice = get_azure_voice("si")
            assert voice is not None
            assert isinstance(voice, str)

    def test_get_azure_voice_tamil(self):
        """Test Tamil language voice selection."""
        voice_map = get_azure_voice_map()

        if "ta" in voice_map:
            voice = get_azure_voice("ta")
            assert voice is not None
            assert isinstance(voice, str)

    def test_get_azure_voice_empty_string(self):
        """Test handling of empty language code."""
        mock_map = {
            "en": "en-US-JennyNeural",
        }

        with patch("adt_press.utils.voices.get_azure_voice_map", return_value=mock_map):
            result = get_azure_voice("")
            assert result is None
