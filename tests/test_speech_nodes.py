"""Tests for speech generation nodes."""

import tempfile
from unittest.mock import patch

from adt_press.models.config import PromptConfig
from adt_press.models.speech import SpeechFile


class TestSpeechFilesNodes:
    """Test speech file generation nodes."""

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
                ),
                SpeechFile(
                    speech_id="text_2",
                    text_id="text_2",
                    language_code="en",
                    speech_path=f"{tmpdir}/en/text_2.mp3",
                ),
                SpeechFile(
                    speech_id="text_1",
                    text_id="text_1",
                    language_code="es",
                    speech_path=f"{tmpdir}/es/text_1.mp3",
                ),
                SpeechFile(
                    speech_id="text_2",
                    text_id="text_2",
                    language_code="es",
                    speech_path=f"{tmpdir}/es/text_2.mp3",
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

    def test_speech_files_none_returns_empty_structure(self):
        """Test that speech_files__none returns proper empty structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config = PromptConfig(
                model="tts-1",
                template_path="prompts/speech_generation.jinja2",
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            plate_translations = {
                "en": {"text_1": "Hello"},
                "es": {"text_1": "Hola"},
                "fr": {"text_1": "Bonjour"},
            }

            from adt_press.nodes.speech_nodes import speech_files__none

            result = speech_files__none(
                run_output_dir_config=tmpdir,
                speech_prompt_config=mock_config,
                plate_translations=plate_translations,
            )

            # Should have empty dict for each language
            assert len(result) == 3
            assert "en" in result
            assert "es" in result
            assert "fr" in result
            assert result["en"] == {}
            assert result["es"] == {}
            assert result["fr"] == {}

    def test_speech_files_tts_handles_single_text(self):
        """Test TTS generation with single text per language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config = PromptConfig(
                model="tts-1",
                template_path="prompts/speech_generation.jinja2",
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            plate_translations = {
                "en": {"single_text": "Just one text"},
            }

            mock_speech_file = SpeechFile(
                speech_id="single_text",
                text_id="single_text",
                language_code="en",
                speech_path=f"{tmpdir}/en/single_text.mp3",
            )

            with patch("adt_press.nodes.speech_nodes.generate_speech_file"):
                with patch("adt_press.nodes.speech_nodes.run_async_task") as mock_async:
                    mock_async.return_value = [mock_speech_file]

                    from adt_press.nodes.speech_nodes import speech_files__tts

                    result = speech_files__tts(
                        run_output_dir_config=tmpdir,
                        speech_prompt_config=mock_config,
                        plate_translations=plate_translations,
                    )

                    assert len(result["en"]) == 1
                    assert "single_text" in result["en"]
                    assert result["en"]["single_text"].text_id == "single_text"
