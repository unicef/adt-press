"""Tests for speech generation LLM module."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from adt_press.llm.speech_generation import generate_speech_file, resolve_voice
from adt_press.models.config import SpeechPromptConfig, SpeechProviderConfig
from adt_press.models.speech import SpeechFile
from adt_press.utils.languages import Language


class TestResolveVoice:
    """Test voice resolution logic."""

    def test_resolve_voice_uses_voice_for_language(self):
        """Test that resolve_voice calls get_voice_for_language with correct params."""
        with patch("adt_press.llm.speech_generation.get_voice_for_language", return_value="test-voice"):
            result = resolve_voice("openai", "en")
            assert result == "test-voice"


class TestGenerateSpeechFile:
    """Test speech file generation."""

    @staticmethod
    def _create_test_config(provider="openai", model="tts-1"):
        """Create a standard test config."""
        return SpeechPromptConfig(
            model=model,
            default_provider=provider,
            providers={
                "openai": SpeechProviderConfig(model="tts-1", languages=["en"]),
                "azure": SpeechProviderConfig(model="azure/speech/azure-tts", languages=["es"]),
            },
            template_path="prompts/speech_generation.jinja2",
            format="mp3",
            bit_rate="64k",
            sample_rate=24000,
        )

    @staticmethod
    def _create_mock_response(content=b"fake_audio_data"):
        """Create a mock response with content attribute."""
        mock_response = MagicMock(spec=["content"])
        mock_response.content = content
        return mock_response

    @pytest.mark.parametrize(
        "provider,model,language_code,expected_provider",
        [
            ("openai", "tts-1", "en", "openai"),
            ("azure", "azure/speech/azure-tts", "es", "azure"),
        ],
    )
    @pytest.mark.asyncio
    async def test_generate_speech_file_success(self, provider, model, language_code, expected_provider):
        """Test successful speech generation for different providers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config(provider, model)
            language = Language(code=language_code, language_code=language_code, name="Test")
            mock_response = self._create_mock_response()

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                    with patch("adt_press.llm.speech_generation.render_template_to_string"):
                        with patch("adt_press.llm.speech_generation.get_voice_for_language", return_value="test-voice"):
                            mock_aspeech.return_value = mock_response
                            mock_segment = MagicMock()
                            mock_audio.from_file.return_value = mock_segment
                            mock_segment.set_frame_rate.return_value = mock_segment

                            result = await generate_speech_file(
                                run_output_dir=tmpdir,
                                config=config,
                                language=language,
                                text_id="test_text",
                                text="Hello world",
                            )

                            assert isinstance(result, SpeechFile)
                            assert result.text_id == "test_text"
                            assert result.language_code == language_code
                            assert result.provider == expected_provider
                            assert result.voice == "test-voice"
                            assert result.model == model

    @pytest.mark.asyncio
    async def test_generate_speech_file_openai_includes_instructions(self):
        """Test that OpenAI models get instructions parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config("openai", "tts-1")
            language = Language(code="en", language_code="en", name="English")

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                    with patch("adt_press.llm.speech_generation.render_template_to_string", return_value="Test prompt"):
                        with patch("adt_press.llm.speech_generation.get_voice_for_language", return_value="alloy"):
                            mock_aspeech.return_value = self._create_mock_response()
                            mock_segment = MagicMock()
                            mock_audio.from_file.return_value = mock_segment
                            mock_segment.set_frame_rate.return_value = mock_segment

                            await generate_speech_file(run_output_dir=tmpdir, config=config, language=language, text_id="test", text="Test")

                            call_kwargs = mock_aspeech.call_args[1]
                            assert "instructions" in call_kwargs
                            assert call_kwargs["instructions"] == "Test prompt"

    @pytest.mark.asyncio
    async def test_generate_speech_file_azure_excludes_instructions(self):
        """Test that Azure models don't get instructions parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config("azure", "azure/speech/azure-tts")
            language = Language(code="es", language_code="es", name="Spanish")

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                    with patch("adt_press.llm.speech_generation.render_template_to_string"):
                        with patch("adt_press.llm.speech_generation.get_voice_for_language", return_value="es-ES-ElviraNeural"):
                            mock_aspeech.return_value = self._create_mock_response()
                            mock_segment = MagicMock()
                            mock_audio.from_file.return_value = mock_segment
                            mock_segment.set_frame_rate.return_value = mock_segment

                            await generate_speech_file(run_output_dir=tmpdir, config=config, language=language, text_id="test", text="Hola")

                            call_kwargs = mock_aspeech.call_args[1]
                            assert "instructions" not in call_kwargs

    @pytest.mark.asyncio
    async def test_generate_speech_file_strips_emojis(self):
        """Test that emojis are stripped from text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config()
            language = Language(code="en", language_code="en", name="English")

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                    with patch("adt_press.llm.speech_generation.render_template_to_string"):
                        with patch("adt_press.llm.speech_generation.get_voice_for_language", return_value="alloy"):
                            with patch("adt_press.llm.speech_generation.strip_emojis", return_value="Hello world"):
                                mock_aspeech.return_value = self._create_mock_response()
                                mock_segment = MagicMock()
                                mock_audio.from_file.return_value = mock_segment
                                mock_segment.set_frame_rate.return_value = mock_segment

                                await generate_speech_file(
                                    run_output_dir=tmpdir,
                                    config=config,
                                    language=language,
                                    text_id="test",
                                    text="Hello 😀 world 🎉",
                                )

                                call_kwargs = mock_aspeech.call_args[1]
                                assert call_kwargs["input"] == "Hello world"

    @pytest.mark.asyncio
    async def test_generate_speech_file_response_write_to_file_method(self):
        """Test handling response with write_to_file() method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config()
            language = Language(code="en", language_code="en", name="English")

            mock_response = MagicMock(spec=["write_to_file"])

            def write_file(path):
                with open(path, "wb") as f:
                    f.write(b"fake_audio_data")

            mock_response.write_to_file = write_file

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                    with patch("adt_press.llm.speech_generation.render_template_to_string"):
                        with patch("adt_press.llm.speech_generation.get_voice_for_language", return_value="alloy"):
                            mock_aspeech.return_value = mock_response
                            mock_segment = MagicMock()
                            mock_audio.from_file.return_value = mock_segment
                            mock_segment.set_frame_rate.return_value = mock_segment

                            result = await generate_speech_file(
                                run_output_dir=tmpdir, config=config, language=language, text_id="test", text="Test"
                            )

                            assert result.speech_id == "test_en"

    @pytest.mark.parametrize("text", ["", "   \n\t   "])
    @pytest.mark.asyncio
    async def test_generate_speech_file_empty_text_error(self, text):
        """Test error when text is empty or whitespace-only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config()
            language = Language(code="en", language_code="en", name="English")

            with pytest.raises(ValueError, match="Empty or whitespace-only text for TTS generation"):
                await generate_speech_file(run_output_dir=tmpdir, config=config, language=language, text_id="test", text=text)

    @pytest.mark.asyncio
    async def test_generate_speech_file_file_not_created_error(self):
        """Test error when TTS output file is not created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config()
            language = Language(code="en", language_code="en", name="English")

            # Mock response that doesn't write a file
            mock_response = self._create_mock_response()

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.render_template_to_string"):
                    with patch("adt_press.llm.speech_generation.get_voice_for_language", return_value="alloy"):
                        mock_aspeech.return_value = mock_response

                        # Mock os.path.exists to return False (file wasn't created)
                        with patch("adt_press.llm.speech_generation.os.path.exists", return_value=False):
                            with pytest.raises(FileNotFoundError, match="TTS output file not created"):
                                await generate_speech_file(
                                    run_output_dir=tmpdir, config=config, language=language, text_id="test", text="Test"
                                )

    @pytest.mark.asyncio
    async def test_generate_speech_file_empty_file_error(self):
        """Test error when TTS output file is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config()
            language = Language(code="en", language_code="en", name="English")

            # Mock response that writes an empty file
            mock_response = MagicMock(spec=["write_to_file"])

            def write_empty_file(path):
                """Write an empty file."""
                with open(path, "wb") as f:
                    f.write(b"")  # Empty content

            mock_response.write_to_file = write_empty_file

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.render_template_to_string"):
                    with patch("adt_press.llm.speech_generation.get_voice_for_language", return_value="alloy"):
                        mock_aspeech.return_value = mock_response

                        # Match the actual error message from the code
                        with pytest.raises(FileNotFoundError, match="TTS output file not created or empty"):
                            await generate_speech_file(run_output_dir=tmpdir, config=config, language=language, text_id="test", text="Test")

    @pytest.mark.parametrize("non_speakable_text", ["—", ".", "..."])
    @pytest.mark.asyncio
    async def test_generate_speech_file_non_speakable_text_empty_audio(self, non_speakable_text):
        """Test that non-speakable text generates empty audio."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config()
            language = Language(code="en", language_code="en", name="English")

            with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                with patch("adt_press.llm.speech_generation.get_voice_for_language", return_value="alloy"):
                    mock_empty = MagicMock()
                    mock_audio.empty.return_value = mock_empty

                    result = await generate_speech_file(
                        run_output_dir=tmpdir,
                        config=config,
                        language=language,
                        text_id="test",
                        text=non_speakable_text,
                    )

                    mock_audio.empty.assert_called_once()
                    mock_empty.export.assert_called_once()
                    assert result.text_id == "test"
                    assert result.language_code == "en"

    @pytest.mark.asyncio
    async def test_generate_speech_file_speakable_short_text_uses_tts(self):
        """Test that short but speakable text uses normal TTS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config()
            language = Language(code="en", language_code="en", name="English")

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                    with patch("adt_press.llm.speech_generation.render_template_to_string"):
                        with patch("adt_press.llm.speech_generation.get_voice_for_language", return_value="alloy"):
                            mock_aspeech.return_value = self._create_mock_response()
                            mock_segment = MagicMock()
                            mock_audio.from_file.return_value = mock_segment
                            mock_segment.set_frame_rate.return_value = mock_segment

                            await generate_speech_file(run_output_dir=tmpdir, config=config, language=language, text_id="test", text="1.")

                            mock_aspeech.assert_called_once()
                            mock_audio.empty.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_speech_file_creates_directory(self):
        """Test that audio directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config()
            language = Language(code="fr", language_code="fr", name="French")

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                    with patch("adt_press.llm.speech_generation.render_template_to_string"):
                        with patch("adt_press.llm.speech_generation.get_voice_for_language", return_value="alloy"):
                            mock_aspeech.return_value = self._create_mock_response()
                            mock_segment = MagicMock()
                            mock_audio.from_file.return_value = mock_segment
                            mock_segment.set_frame_rate.return_value = mock_segment

                            await generate_speech_file(
                                run_output_dir=tmpdir, config=config, language=language, text_id="test", text="Bonjour"
                            )

                            audio_dir = os.path.join(tmpdir, "audio", "fr")
                            assert os.path.exists(audio_dir)

    @pytest.mark.asyncio
    async def test_generate_speech_file_unsupported_provider_error(self):
        """Test error when provider doesn't support TTS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config()
            language = Language(code="en", language_code="en", name="English")

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.render_template_to_string"):
                    with patch("adt_press.llm.speech_generation.get_voice_for_language", return_value="alloy"):
                        # Simulate litellm error for unsupported provider
                        # Since the code doesn't catch this yet, we expect the raw Exception
                        mock_aspeech.side_effect = Exception("Unable to map the custom llm provider=elevenlabs to a known provider")

                        # The code doesn't handle this error yet, so it bubbles up as Exception
                        with pytest.raises(Exception, match="Unable to map the custom llm provider"):
                            await generate_speech_file(run_output_dir=tmpdir, config=config, language=language, text_id="test", text="Test")
