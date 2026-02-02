"""Tests for speech generation nodes."""

import tempfile
from unittest.mock import patch

from adt_press.models.config import PromptConfig, SpeechPromptConfig, SpeechProviderConfig
from adt_press.models.speech import SpeechFile


class TestSpeechFilesNodes:
    """Test speech file generation nodes."""

    @staticmethod
    def _create_mock_voice_maps():
        """Create mock voice maps for testing."""
        return {
            "openai": {"en": "alloy", "es": "alloy", "default": "alloy"},
            "azure": {"es": "es-ES-ElviraNeural", "default": "en-US-JennyNeural"},
        }

    def test_speech_files_tts_with_multiple_languages(self):
        """Test TTS speech file generation with multiple languages and texts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock config
            mock_config = PromptConfig(
                model="tts-1",
                template_path="prompts/speech_generation.jinja2",
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            voice_maps = self._create_mock_voice_maps()

            # Sample translations with multiple languages and texts
            plate_translations = {
                "en": {
                    "text_1": "Hello world",
                    "text_2": "Good morning",
                },
                "es": {
                    "text_1": "Hola mundo",
                    "text_2": "Buenos días",
                },
            }

            # Mock speech files that would be returned
            mock_speech_files = [
                SpeechFile(
                    speech_id="text_1",
                    text_id="text_1",
                    language_code="en",
                    speech_path=f"{tmpdir}/en/text_1.mp3",
                    provider="openai",
                    voice="alloy",
                    model="tts-1",
                ),
                SpeechFile(
                    speech_id="text_2",
                    text_id="text_2",
                    language_code="en",
                    speech_path=f"{tmpdir}/en/text_2.mp3",
                    provider="openai",
                    voice="alloy",
                    model="tts-1",
                ),
                SpeechFile(
                    speech_id="text_1",
                    text_id="text_1",
                    language_code="es",
                    speech_path=f"{tmpdir}/es/text_1.mp3",
                    provider="openai",
                    voice="alloy",
                    model="tts-1",
                ),
                SpeechFile(
                    speech_id="text_2",
                    text_id="text_2",
                    language_code="es",
                    speech_path=f"{tmpdir}/es/text_2.mp3",
                    provider="openai",
                    voice="alloy",
                    model="tts-1",
                ),
            ]

            with patch("adt_press.nodes.speech_nodes.generate_speech_file"):
                with patch("adt_press.nodes.speech_nodes.run_async_task") as mock_async:
                    # Mock the async task runner to return speech files
                    mock_async.return_value = mock_speech_files

                    # Import and call the function
                    from adt_press.nodes.speech_nodes import speech_files__tts

                    result = speech_files__tts(
                        run_output_dir_config=tmpdir,
                        speech_prompt_config=mock_config,
                        voice_maps_config=voice_maps,
                        speech_instructions_config={"default": "Speak in a cheerful tone."},
                        plate_translations=plate_translations,
                    )

                    # Verify structure - should have dicts for each language
                    assert "en" in result
                    assert "es" in result
                    assert "text_1" in result["en"]
                    assert "text_2" in result["en"]
                    assert "text_1" in result["es"]
                    assert "text_2" in result["es"]

                    # Verify correct files were mapped
                    assert result["en"]["text_1"].language_code == "en"
                    assert result["es"]["text_1"].language_code == "es"

    def test_speech_files_tts_handles_single_text(self):
        """Test TTS generation with single text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config = PromptConfig(
                model="tts-1",
                template_path="prompts/speech_generation.jinja2",
                rate_limit=10,
            )

            voice_maps = self._create_mock_voice_maps()

            plate_translations = {
                "en": {
                    "text_1": "Hello",
                },
            }

            mock_speech_files = [
                SpeechFile(
                    speech_id="text_1",
                    text_id="text_1",
                    language_code="en",
                    speech_path=f"{tmpdir}/en/text_1.mp3",
                    provider="openai",
                    voice="alloy",
                    model="tts-1",
                ),
            ]

            with patch("adt_press.nodes.speech_nodes.generate_speech_file"):
                with patch("adt_press.nodes.speech_nodes.run_async_task") as mock_async:
                    mock_async.return_value = mock_speech_files

                    from adt_press.nodes.speech_nodes import speech_files__tts

                    result = speech_files__tts(
                        run_output_dir_config=tmpdir,
                        speech_prompt_config=mock_config,
                        voice_maps_config=voice_maps,
                        speech_instructions_config={"default": "Speak in a cheerful tone."},
                        plate_translations=plate_translations,
                    )

                    assert "en" in result
                    assert "text_1" in result["en"]
                    assert result["en"]["text_1"].text_id == "text_1"

    def test_speech_files_with_mixed_providers(self):
        """Test speech file generation with mixed TTS providers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config that uses different providers per language
            mock_config = SpeechPromptConfig(
                model="tts-1",
                template_path="prompts/speech_generation.jinja2",
                provider="dynamic",
                default_provider="openai",
                providers={
                    "openai": SpeechProviderConfig(model="tts-1", languages=["en"]),
                    "azure": SpeechProviderConfig(model="azure/speech/azure-tts", languages=["es"]),
                },
            )

            voice_maps = self._create_mock_voice_maps()

            plate_translations = {
                "en": {"text_1": "Hello"},
                "es": {"text_1": "Hola"},
            }

            mock_speech_files = [
                SpeechFile(
                    speech_id="text_1",
                    text_id="text_1",
                    language_code="en",
                    speech_path=f"{tmpdir}/en/text_1.mp3",
                    provider="openai",
                    voice="alloy",
                    model="tts-1",
                ),
                SpeechFile(
                    speech_id="text_1",
                    text_id="text_1",
                    language_code="es",
                    speech_path=f"{tmpdir}/es/text_1.mp3",
                    provider="azure",
                    voice="es-ES-ElviraNeural",
                    model="azure/speech/azure-tts",
                ),
            ]

            with patch("adt_press.nodes.speech_nodes.generate_speech_file"):
                with patch("adt_press.nodes.speech_nodes.run_async_task") as mock_async:
                    mock_async.return_value = mock_speech_files

                    from adt_press.nodes.speech_nodes import speech_files__tts

                    result = speech_files__tts(
                        run_output_dir_config=tmpdir,
                        speech_prompt_config=mock_config,
                        voice_maps_config=voice_maps,
                        speech_instructions_config={"default": "Speak in a cheerful tone."},
                        plate_translations=plate_translations,
                    )

                    # Verify providers were used correctly
                    assert result["en"]["text_1"].provider == "openai"
                    assert result["es"]["text_1"].provider == "azure"
