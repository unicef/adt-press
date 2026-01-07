"""Tests for SpeechPromptConfig configuration model."""

from adt_press.models.config import SpeechPromptConfig, SpeechProviderConfig


class TestSpeechPromptConfigProviderSelection:
    """Test per-language provider selection logic."""

    def test_get_provider_for_language_exact_match(self):
        """Test exact language code match returns correct provider."""
        config = SpeechPromptConfig(
            model="default",
            template_path="prompts/speech_generation.jinja2",
            default_provider="openai",
            providers={
                "openai": SpeechProviderConfig(model="tts-1", languages=["en"]),
                "azure": SpeechProviderConfig(model="azure/speech/azure-tts", languages=["es"]),
            },
        )

        assert config.get_provider_for_language("es") == "azure"
        assert config.get_provider_for_language("en") == "openai"

    def test_get_provider_for_language_base_language_match(self):
        """Test base language match for locale codes (es-uy -> es)."""
        config = SpeechPromptConfig(
            model="default",
            template_path="prompts/speech_generation.jinja2",
            default_provider="openai",
            providers={
                "openai": SpeechProviderConfig(model="tts-1", languages=["en"]),
                "azure": SpeechProviderConfig(model="azure/speech/azure-tts", languages=["es", "si"]),
            },
        )

        # Locales should match base language
        assert config.get_provider_for_language("es-uy") == "azure"
        assert config.get_provider_for_language("es-mx") == "azure"
        assert config.get_provider_for_language("si-lk") == "azure"

    def test_get_provider_for_language_exact_takes_precedence(self):
        """Test exact match takes precedence over base language match."""
        config = SpeechPromptConfig(
            model="default",
            template_path="prompts/speech_generation.jinja2",
            default_provider="openai",
            providers={
                "openai": SpeechProviderConfig(model="tts-1", languages=["en", "es-mx"]),
                "azure": SpeechProviderConfig(model="azure/speech/azure-tts", languages=["es"]),
            },
        )

        # Base Spanish uses Azure
        assert config.get_provider_for_language("es") == "azure"
        assert config.get_provider_for_language("es-uy") == "azure"

        # But Mexican Spanish explicitly uses OpenAI
        assert config.get_provider_for_language("es-mx") == "openai"

    def test_get_provider_for_language_fallback_to_default(self):
        """Test fallback to default provider when no match found."""
        config = SpeechPromptConfig(
            model="default",
            template_path="prompts/speech_generation.jinja2",
            default_provider="openai",
            providers={
                "openai": SpeechProviderConfig(model="tts-1", languages=["en"]),
                "azure": SpeechProviderConfig(model="azure/speech/azure-tts", languages=["es"]),
            },
        )

        # French not in map, should use default
        assert config.get_provider_for_language("fr") == "openai"
        assert config.get_provider_for_language("fr-fr") == "openai"

    def test_get_provider_for_language_empty_providers(self):
        """Test empty providers dict uses default provider."""
        config = SpeechPromptConfig(
            model="default",
            template_path="prompts/speech_generation.jinja2",
            default_provider="openai",
            providers={
                "openai": SpeechProviderConfig(model="tts-1", languages=[]),
            },
        )

        assert config.get_provider_for_language("en") == "openai"
        assert config.get_provider_for_language("es") == "openai"

    def test_get_provider_for_language_azure_default(self):
        """Test fallback when default provider is azure."""
        config = SpeechPromptConfig(
            model="default",
            template_path="prompts/speech_generation.jinja2",
            default_provider="azure",
            providers={
                "openai": SpeechProviderConfig(model="tts-1", languages=["en"]),
                "azure": SpeechProviderConfig(model="azure/speech/azure-tts", languages=[]),
            },
        )

        # English explicitly uses OpenAI
        assert config.get_provider_for_language("en") == "openai"

        # Others fall back to Azure default
        assert config.get_provider_for_language("es") == "azure"
        assert config.get_provider_for_language("fr") == "azure"

    def test_get_active_config_with_language_code(self):
        """Test get_active_config uses language-specific provider."""
        config = SpeechPromptConfig(
            model="default",
            template_path="prompts/speech_generation.jinja2",
            default_provider="openai",
            providers={
                "openai": SpeechProviderConfig(model="tts-1", languages=["en"]),
                "azure": SpeechProviderConfig(model="azure/speech/azure-tts", languages=["es"]),
            },
        )

        # English uses default OpenAI
        model = config.get_active_config("en")
        assert model == "tts-1"

        # Spanish uses Azure
        model = config.get_active_config("es")
        assert model == "azure/speech/azure-tts"

    def test_get_active_config_with_locale_code(self):
        """Test get_active_config with locale codes."""
        config = SpeechPromptConfig(
            model="default",
            template_path="prompts/speech_generation.jinja2",
            default_provider="openai",
            providers={
                "openai": SpeechProviderConfig(model="tts-1", languages=["en"]),
                "azure": SpeechProviderConfig(model="azure/speech/azure-tts", languages=["es", "si"]),
            },
        )

        # Locale codes should match base language
        model = config.get_active_config("es-uy")
        assert model == "azure/speech/azure-tts"

        model = config.get_active_config("si-lk")
        assert model == "azure/speech/azure-tts"

    def test_get_active_config_without_language_code(self):
        """Test get_active_config without language code uses default provider."""
        config = SpeechPromptConfig(
            model="default",
            template_path="prompts/speech_generation.jinja2",
            default_provider="azure",
            providers={
                "openai": SpeechProviderConfig(model="tts-1", languages=["en"]),
                "azure": SpeechProviderConfig(model="azure/speech/azure-tts", languages=[]),
            },
        )

        # Without language_code, should use default provider (azure)
        model = config.get_active_config()
        assert model == "azure/speech/azure-tts"

    def test_empty_language_list(self):
        """Test empty languages list uses default provider."""
        config = SpeechPromptConfig(
            model="default",
            template_path="prompts/speech_generation.jinja2",
            default_provider="openai",
            providers={
                "openai": SpeechProviderConfig(model="tts-1", languages=[]),
                "azure": SpeechProviderConfig(model="azure/speech/azure-tts", languages=[]),
            },
        )

        assert config.get_provider_for_language("es") == "openai"
        assert config.get_provider_for_language("en") == "openai"
        assert config.get_provider_for_language("si-lk") == "openai"
