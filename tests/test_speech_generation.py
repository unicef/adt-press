"""Tests for speech generation LLM module."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from adt_press.llm.speech_generation import generate_speech_file, resolve_voice
from adt_press.models.config import SpeechPromptConfig
from adt_press.models.speech import SpeechFile
from adt_press.utils.languages import Language


class TestResolveVoice:
    """Test voice resolution logic."""

    def test_resolve_voice_auto_azure_with_match(self):
        """Test auto voice selection for Azure with language match."""
        with patch("adt_press.llm.speech_generation.get_azure_voice", return_value="si-LK-SameeraNeural"):
            result = resolve_voice("azure/speech/azure-tts", "auto", "si")
            assert result == "si-LK-SameeraNeural"

    def test_resolve_voice_auto_azure_no_match_fallback(self):
        """Test auto voice selection for Azure with no language match falls back to English."""
        with patch("adt_press.llm.speech_generation.get_azure_voice", return_value=None):
            result = resolve_voice("azure/speech/azure-tts", "auto", "xx")
            assert result == "en-US-JennyNeural"

    def test_resolve_voice_auto_openai(self):
        """Test auto voice selection for OpenAI defaults to alloy."""
        result = resolve_voice("tts-1", "auto", "en")
        assert result == "alloy"

    def test_resolve_voice_azure_explicit_valid_voice(self):
        """Test explicit Azure voice is used when valid."""
        result = resolve_voice("azure/speech/azure-tts", "es-ES-ElviraNeural", "es")
        assert result == "es-ES-ElviraNeural"

    def test_resolve_voice_azure_invalid_voice_fallback(self):
        """Test Azure model with invalid voice falls back to language match."""
        with patch("adt_press.llm.speech_generation.get_azure_voice", return_value="fr-FR-DeniseNeural"):
            result = resolve_voice("azure/speech/azure-tts", "alloy", "fr")
            assert result == "fr-FR-DeniseNeural"

    def test_resolve_voice_azure_invalid_voice_no_match_fallback(self):
        """Test Azure model with invalid voice and no match falls back to English."""
        with patch("adt_press.llm.speech_generation.get_azure_voice", return_value=None):
            result = resolve_voice("azure/speech/azure-tts", "alloy", "xx")
            assert result == "en-US-JennyNeural"

    def test_resolve_voice_openai_explicit_valid_voice(self):
        """Test explicit OpenAI voice is used when valid."""
        with patch("adt_press.llm.speech_generation.get_openai_voices", return_value=["alloy", "echo", "nova"]):
            result = resolve_voice("tts-1", "nova", "en")
            assert result == "nova"

    def test_resolve_voice_openai_invalid_voice_fallback(self):
        """Test OpenAI model with Azure voice falls back to alloy."""
        with patch("adt_press.llm.speech_generation.get_openai_voices", return_value=["alloy", "echo", "nova"]):
            result = resolve_voice("tts-1", "es-ES-ElviraNeural", "es")
            assert result == "alloy"


class TestGenerateSpeechFile:
    """Test speech file generation."""

    def _create_mock_response_that_writes_file(self, content=b"fake_audio_data"):
        """Helper to create a mock response that actually writes files."""
        mock_response = MagicMock()
        mock_response.content = content
        # Don't mock write_to_file or read - let them not exist so code uses content
        if hasattr(mock_response, "write_to_file"):
            del mock_response.write_to_file
        if hasattr(mock_response, "read"):
            del mock_response.read
        return mock_response

    @pytest.mark.asyncio
    async def test_generate_speech_file_openai_success(self):
        """Test successful speech generation with OpenAI model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            config = SpeechPromptConfig(
                model="tts-1",
                provider="openai",
                openai=SpeechProviderConfig(model="tts-1", voice="alloy"),
                template_path="prompts/speech_generation.jinja2",
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            language = Language(code="en", language_code="en", name="English")

            mock_response = self._create_mock_response_that_writes_file()

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                    with patch("adt_press.llm.speech_generation.render_template_to_string") as mock_render:
                        mock_aspeech.return_value = mock_response
                        mock_render.return_value = "Test instructions"

                        mock_segment = MagicMock()
                        mock_audio.from_mp3.return_value = mock_segment
                        mock_segment.set_frame_rate.return_value = mock_segment

                        result = await generate_speech_file(
                            run_output_dir=tmpdir,
                            config=config,
                            language=language,
                            text_id="test_text",
                            text="Hello world",
                        )

                        # Verify result
                        assert isinstance(result, SpeechFile)
                        assert result.speech_id == "test_text_en"
                        assert result.text_id == "test_text"
                        assert result.language_code == "en"
                        assert "audio/en/" in result.speech_path
                        assert result.provider == "openai"
                        assert result.voice == "alloy"
                        assert result.model == "tts-1"

                        # Verify aspeech was called with correct parameters
                        call_kwargs = mock_aspeech.call_args[1]
                        assert call_kwargs["model"] == "tts-1"
                        assert call_kwargs["voice"] == "alloy"
                        assert call_kwargs["input"] == "Hello world"
                        assert "instructions" in call_kwargs

    @pytest.mark.asyncio
    async def test_generate_speech_file_azure_success(self):
        """Test successful speech generation with Azure model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            config = SpeechPromptConfig(
                model="azure/speech/azure-tts",
                provider="azure",
                azure=SpeechProviderConfig(model="azure/speech/azure-tts", voice="auto"),
                template_path="prompts/speech_generation.jinja2",
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            language = Language(code="es", language_code="es", name="Spanish")

            mock_response = self._create_mock_response_that_writes_file()

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                    with patch("adt_press.llm.speech_generation.render_template_to_string"):
                        with patch("adt_press.llm.speech_generation.get_azure_voice", return_value="es-ES-ElviraNeural"):
                            mock_aspeech.return_value = mock_response

                            mock_segment = MagicMock()
                            mock_audio.from_mp3.return_value = mock_segment
                            mock_segment.set_frame_rate.return_value = mock_segment

                            result = await generate_speech_file(
                                run_output_dir=tmpdir,
                                config=config,
                                language=language,
                                text_id="test_text",
                                text="Hola mundo",
                            )

                            # Verify Azure doesn't get instructions parameter
                            call_kwargs = mock_aspeech.call_args[1]
                            assert "instructions" not in call_kwargs
                            assert call_kwargs["voice"] == "es-ES-ElviraNeural"

                            assert result.provider == "azure"
                            assert result.voice == "es-ES-ElviraNeural"
                            assert result.model == "azure/speech/azure-tts"

    @pytest.mark.asyncio
    async def test_generate_speech_file_strips_emojis(self):
        """Test that emojis are stripped from text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            config = SpeechPromptConfig(
                model="tts-1",
                provider="openai",
                openai=SpeechProviderConfig(model="tts-1", voice="alloy"),
                template_path="prompts/speech_generation.jinja2",
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            language = Language(code="en", language_code="en", name="English")

            mock_response = self._create_mock_response_that_writes_file()

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                    with patch("adt_press.llm.speech_generation.render_template_to_string"):
                        with patch("adt_press.llm.speech_generation.strip_emojis", return_value="Hello world"):
                            mock_aspeech.return_value = mock_response

                            mock_segment = MagicMock()
                            mock_audio.from_mp3.return_value = mock_segment
                            mock_segment.set_frame_rate.return_value = mock_segment

                            result = await generate_speech_file(
                                run_output_dir=tmpdir,
                                config=config,
                                language=language,
                                text_id="test",
                                text="Hello 😀 world 🎉",
                            )

                            # Verify stripped text was used
                            call_kwargs = mock_aspeech.call_args[1]
                            assert call_kwargs["input"] == "Hello world"

                            assert result.provider == "openai"
                            assert result.voice == "alloy"
                            assert result.model == "tts-1"

    @pytest.mark.asyncio
    async def test_generate_speech_file_response_read_method(self):
        """Test handling response with read() method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            config = SpeechPromptConfig(
                model="tts-1",
                provider="openai",
                openai=SpeechProviderConfig(model="tts-1", voice="alloy"),
                template_path="prompts/speech_generation.jinja2",
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            language = Language(code="en", language_code="en", name="English")

            # Mock response with ONLY read() method - use spec to control attributes
            mock_response = MagicMock(spec=["read"])
            mock_response.read.return_value = b"fake_audio_data"

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                    with patch("adt_press.llm.speech_generation.render_template_to_string"):
                        mock_aspeech.return_value = mock_response

                        mock_segment = MagicMock()
                        mock_audio.from_mp3.return_value = mock_segment
                        mock_segment.set_frame_rate.return_value = mock_segment

                        result = await generate_speech_file(
                            run_output_dir=tmpdir,
                            config=config,
                            language=language,
                            text_id="test",
                            text="Test",
                        )

                        assert result.speech_id == "test_en"
                        # Verify read() was called
                        mock_response.read.assert_called_once()

                        assert result.provider == "openai"
                        assert result.voice == "alloy"
                        assert result.model == "tts-1"

    @pytest.mark.asyncio
    async def test_generate_speech_file_file_not_created_error(self):
        """Test error when TTS output file is not created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            config = SpeechPromptConfig(
                model="tts-1",
                provider="openai",
                openai=SpeechProviderConfig(model="tts-1", voice="alloy"),
                template_path="prompts/speech_generation.jinja2",
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            language = Language(code="en", language_code="en", name="English")

            mock_response = self._create_mock_response_that_writes_file()

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.render_template_to_string"):
                    # Mock os.path.exists to return False after file write attempt
                    with patch("adt_press.llm.speech_generation.os.path.exists", return_value=False):
                        mock_aspeech.return_value = mock_response

                        with pytest.raises(FileNotFoundError, match="TTS output file not created"):
                            await generate_speech_file(
                                run_output_dir=tmpdir,
                                config=config,
                                language=language,
                                text_id="test",
                                text="Test",
                            )

    @pytest.mark.asyncio
    async def test_generate_speech_file_empty_file_error(self):
        """Test error when TTS output file is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            config = SpeechPromptConfig(
                model="tts-1",
                provider="openai",
                openai=SpeechProviderConfig(model="tts-1", voice="alloy"),
                template_path="prompts/speech_generation.jinja2",
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            language = Language(code="en", language_code="en", name="English")

            mock_response = self._create_mock_response_that_writes_file(content=b"")

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.render_template_to_string"):
                    mock_aspeech.return_value = mock_response

                    with pytest.raises(ValueError, match="TTS output file is empty"):
                        await generate_speech_file(
                            run_output_dir=tmpdir,
                            config=config,
                            language=language,
                            text_id="test",
                            text="Test",
                        )

    @pytest.mark.asyncio
    async def test_generate_speech_file_creates_directory(self):
        """Test that audio directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            config = SpeechPromptConfig(
                model="tts-1",
                provider="openai",
                openai=SpeechProviderConfig(model="tts-1", voice="alloy"),
                template_path="prompts/speech_generation.jinja2",
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            language = Language(code="fr", language_code="fr", name="French")

            mock_response = self._create_mock_response_that_writes_file()

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                    with patch("adt_press.llm.speech_generation.render_template_to_string"):
                        mock_aspeech.return_value = mock_response

                        mock_segment = MagicMock()
                        mock_audio.from_mp3.return_value = mock_segment
                        mock_segment.set_frame_rate.return_value = mock_segment

                        result = await generate_speech_file(
                            run_output_dir=tmpdir,
                            config=config,
                            language=language,
                            text_id="test",
                            text="Bonjour",
                        )

                        # Verify directory was created
                        audio_dir = os.path.join(tmpdir, "audio", "fr")
                        assert os.path.exists(audio_dir)
                        assert result.language_code == "fr"

                        assert result.provider == "openai"
                        assert result.voice == "alloy"
                        assert result.model == "tts-1"

    @pytest.mark.asyncio
    async def test_generate_speech_file_response_write_to_file_method(self):
        """Test handling response with write_to_file() method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            config = SpeechPromptConfig(
                model="tts-1",
                provider="openai",
                openai=SpeechProviderConfig(model="tts-1", voice="alloy"),
                template_path="prompts/speech_generation.jinja2",
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            language = Language(code="en", language_code="en", name="English")

            # Mock response with write_to_file method
            mock_response = MagicMock(spec=["write_to_file"])

            def write_file(path):
                """Actually write a file when write_to_file is called."""
                with open(path, "wb") as f:
                    f.write(b"fake_audio_data")

            mock_response.write_to_file = write_file

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                    with patch("adt_press.llm.speech_generation.render_template_to_string"):
                        mock_aspeech.return_value = mock_response

                        mock_segment = MagicMock()
                        mock_audio.from_mp3.return_value = mock_segment
                        mock_segment.set_frame_rate.return_value = mock_segment

                        result = await generate_speech_file(
                            run_output_dir=tmpdir,
                            config=config,
                            language=language,
                            text_id="test",
                            text="Test",
                        )

                        assert result.speech_id == "test_en"
                        assert result.provider == "openai"
                        assert result.voice == "alloy"
                        assert result.model == "tts-1"

    @pytest.mark.asyncio
    async def test_generate_speech_file_response_async_content(self):
        """Test handling response with async content attribute."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            config = SpeechPromptConfig(
                model="tts-1",
                provider="openai",
                openai=SpeechProviderConfig(model="tts-1", voice="alloy"),
                template_path="prompts/speech_generation.jinja2",
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            language = Language(code="en", language_code="en", name="English")

            # Create an async coroutine that returns content
            async def async_content():
                return b"fake_audio_data"

            # Mock response with content that has __await__ (is awaitable)
            mock_response = MagicMock(spec=["content"])
            mock_response.content = async_content()

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                    with patch("adt_press.llm.speech_generation.render_template_to_string"):
                        mock_aspeech.return_value = mock_response

                        mock_segment = MagicMock()
                        mock_audio.from_mp3.return_value = mock_segment
                        mock_segment.set_frame_rate.return_value = mock_segment

                        result = await generate_speech_file(
                            run_output_dir=tmpdir,
                            config=config,
                            language=language,
                            text_id="test",
                            text="Test",
                        )

                        assert result.speech_id == "test_en"
                        assert result.provider == "openai"
                        assert result.voice == "alloy"
                        assert result.model == "tts-1"

    @pytest.mark.asyncio
    async def test_generate_speech_file_response_iter_bytes(self):
        """Test handling response with iter_bytes() streaming method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            config = SpeechPromptConfig(
                model="tts-1",
                provider="openai",
                openai=SpeechProviderConfig(model="tts-1", voice="alloy"),
                template_path="prompts/speech_generation.jinja2",
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            language = Language(code="en", language_code="en", name="English")

            # Mock response with iter_bytes async generator
            async def fake_iter_bytes():
                """Async generator that yields audio chunks."""
                yield b"fake_"
                yield b"audio_"
                yield b"data"

            mock_response = MagicMock(spec=["iter_bytes"])
            mock_response.iter_bytes = fake_iter_bytes

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                    with patch("adt_press.llm.speech_generation.render_template_to_string"):
                        mock_aspeech.return_value = mock_response

                        mock_segment = MagicMock()
                        mock_audio.from_mp3.return_value = mock_segment
                        mock_segment.set_frame_rate.return_value = mock_segment

                        result = await generate_speech_file(
                            run_output_dir=tmpdir,
                            config=config,
                            language=language,
                            text_id="test",
                            text="Test",
                        )

                        assert result.speech_id == "test_en"
                        assert result.provider == "openai"
                        assert result.voice == "alloy"
                        assert result.model == "tts-1"

                        # Verify the chunks were written correctly
                        raw_path = os.path.join(tmpdir, "audio", "en", "test_en_raw.mp3")
                        with open(raw_path, "rb") as f:
                            assert f.read() == b"fake_audio_data"

    @pytest.mark.asyncio
    async def test_generate_speech_file_unknown_response_type_error(self):
        """Test error when response has unknown type (no recognized attributes)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            config = SpeechPromptConfig(
                model="tts-1",
                provider="openai",
                openai=SpeechProviderConfig(model="tts-1", voice="alloy"),
                template_path="prompts/speech_generation.jinja2",
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            language = Language(code="en", language_code="en", name="English")

            # Mock response with NO recognized attributes
            mock_response = MagicMock(spec=["some_unknown_method"])

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.render_template_to_string"):
                    mock_aspeech.return_value = mock_response

                    with pytest.raises(ValueError, match="Unknown response type"):
                        await generate_speech_file(
                            run_output_dir=tmpdir,
                            config=config,
                            language=language,
                            text_id="test",
                            text="Test",
                        )

    @pytest.mark.asyncio
    async def test_generate_speech_file_write_exception_handling(self):
        """Test exception handling during file write."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            config = SpeechPromptConfig(
                model="tts-1",
                provider="openai",
                openai=SpeechProviderConfig(model="tts-1", voice="alloy"),
                template_path="prompts/speech_generation.jinja2",
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            language = Language(code="en", language_code="en", name="English")

            # Mock response that raises an exception when trying to write
            mock_response = MagicMock(spec=["content"])
            mock_response.content = property(lambda self: (_ for _ in ()).throw(IOError("Disk full")))

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.render_template_to_string"):
                    mock_aspeech.return_value = mock_response

                    with pytest.raises(ValueError, match="Failed to write TTS response to file"):
                        await generate_speech_file(
                            run_output_dir=tmpdir,
                            config=config,
                            language=language,
                            text_id="test",
                            text="Test",
                        )

    @pytest.mark.asyncio
    async def test_generate_speech_file_empty_text_error(self):
        """Test error when text is empty or whitespace-only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            config = SpeechPromptConfig(
                model="tts-1",
                provider="openai",
                openai=SpeechProviderConfig(model="tts-1", voice="alloy"),
                template_path="prompts/speech_generation.jinja2",
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            language = Language(code="en", language_code="en", name="English")

            # Test empty string
            with pytest.raises(ValueError, match="Empty or whitespace-only text for TTS generation"):
                await generate_speech_file(
                    run_output_dir=tmpdir,
                    config=config,
                    language=language,
                    text_id="test",
                    text="",
                )

            # Test whitespace-only string
            with pytest.raises(ValueError, match="Empty or whitespace-only text for TTS generation"):
                await generate_speech_file(
                    run_output_dir=tmpdir,
                    config=config,
                    language=language,
                    text_id="test",
                    text="   \n\t   ",
                )

    @pytest.mark.asyncio
    async def test_generate_speech_file_non_speakable_text_silent_audio(self):
        """Test that non-speakable text (punctuation-only) generates silent audio."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            config = SpeechPromptConfig(
                model="azure/speech/azure-tts",
                provider="azure",
                azure=SpeechProviderConfig(model="azure/speech/azure-tts", voice="en-US-JennyNeural"),
                template_path="prompts/speech_generation.jinja2",
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            language = Language(code="en", language_code="en", name="English")

            # Mock AudioSegment for silent audio generation
            with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                mock_silent = MagicMock()
                mock_audio.silent.return_value = mock_silent

                # Test with em-dash (punctuation-only)
                result = await generate_speech_file(
                    run_output_dir=tmpdir,
                    config=config,
                    language=language,
                    text_id="test_emdash",
                    text="—",
                )

                # Verify silent audio was created
                mock_audio.silent.assert_called_once_with(duration=50)
                mock_silent.export.assert_called_once()

                # Verify result
                assert result.text_id == "test_emdash"
                assert result.language_code == "en"
                assert result.speech_id == "test_emdash_en"
                assert result.speech_path.endswith("test_emdash_en.mp3")
                assert result.provider == "azure"
                assert result.model == "azure/speech/azure-tts"

    @pytest.mark.asyncio
    async def test_generate_speech_file_non_speakable_text_period(self):
        """Test that a single period generates silent audio."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            config = SpeechPromptConfig(
                model="tts-1",
                provider="openai",
                openai=SpeechProviderConfig(model="tts-1", voice="alloy"),
                template_path="prompts/speech_generation.jinja2",
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            language = Language(code="si", language_code="si", name="Sinhala")

            with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                mock_silent = MagicMock()
                mock_audio.silent.return_value = mock_silent

                result = await generate_speech_file(
                    run_output_dir=tmpdir,
                    config=config,
                    language=language,
                    text_id="test_period",
                    text=".",
                )

                # Verify silent audio was created
                mock_audio.silent.assert_called_once_with(duration=50)
                assert result.language_code == "si"
                assert result.speech_id == "test_period_si"
                assert result.speech_path.endswith("test_period_si.mp3")

    @pytest.mark.asyncio
    async def test_generate_speech_file_speakable_short_text(self):
        """Test that short but speakable text (like '1.') goes through normal TTS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            config = SpeechPromptConfig(
                model="tts-1",
                provider="openai",
                openai=SpeechProviderConfig(model="tts-1", voice="alloy"),
                template_path="prompts/speech_generation.jinja2",
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
                rate_limit=10,
                max_retries=3,
                timeout=120,
            )

            language = Language(code="en", language_code="en", name="English")

            mock_response = self._create_mock_response_that_writes_file()

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                    with patch("adt_press.llm.speech_generation.render_template_to_string"):
                        mock_aspeech.return_value = mock_response

                        mock_segment = MagicMock()
                        mock_audio.from_mp3.return_value = mock_segment
                        mock_segment.set_frame_rate.return_value = mock_segment

                        # Test with "1." - should call TTS API, not generate silent audio
                        result = await generate_speech_file(
                            run_output_dir=tmpdir,
                            config=config,
                            language=language,
                            text_id="test_number",
                            text="1.",
                        )

                        # Verify TTS API was called (not silent audio)
                        mock_aspeech.assert_called_once()
                        call_kwargs = mock_aspeech.call_args[1]
                        assert call_kwargs["input"] == "1."

                        # Verify AudioSegment.silent was NOT called
                        mock_audio.silent.assert_not_called()

                        assert result.text_id == "test_number"

    @pytest.mark.asyncio
    async def test_generate_speech_file_per_language_provider_selection(self):
        """Test that language-specific provider is used during generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            # Configure Spanish to use Azure
            config = SpeechPromptConfig(
                model="default",
                template_path="prompts/speech_generation.jinja2",
                provider="openai",  # Default is OpenAI
                language_providers={"es": "azure"},  # But Spanish uses Azure
                openai=SpeechProviderConfig(model="tts-1", voice="alloy"),
                azure=SpeechProviderConfig(model="azure/speech/azure-tts", voice="auto"),
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
            )

            language = Language(code="es", language_code="es", name="Spanish")
            mock_response = self._create_mock_response_that_writes_file()

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                    with patch("adt_press.llm.speech_generation.render_template_to_string"):
                        with patch("adt_press.llm.speech_generation.get_azure_voice", return_value="es-ES-ElviraNeural"):
                            mock_aspeech.return_value = mock_response

                            mock_segment = MagicMock()
                            mock_audio.from_mp3.return_value = mock_segment
                            mock_segment.set_frame_rate.return_value = mock_segment

                            result = await generate_speech_file(
                                run_output_dir=tmpdir,
                                config=config,
                                language=language,
                                text_id="test_text",
                                text="Hola mundo",
                            )

                            # Verify Azure was used (no instructions parameter)
                            call_kwargs = mock_aspeech.call_args[1]
                            assert "instructions" not in call_kwargs
                            assert call_kwargs["model"] == "azure/speech/azure-tts"
                            assert call_kwargs["voice"] == "es-ES-ElviraNeural"

                            assert result.provider == "azure"  # Note: Config stores default, not resolved
                            assert result.model == "azure/speech/azure-tts"

    @pytest.mark.asyncio
    async def test_generate_speech_file_locale_code_provider_selection(self):
        """Test that locale codes (es-uy, si-lk) match base language provider."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            config = SpeechPromptConfig(
                model="default",
                template_path="prompts/speech_generation.jinja2",
                provider="openai",
                language_providers={"es": "azure"},  # Spanish (all locales) uses Azure
                openai=SpeechProviderConfig(model="tts-1", voice="alloy"),
                azure=SpeechProviderConfig(model="azure/speech/azure-tts", voice="auto"),
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
            )

            # Test with Uruguayan Spanish locale
            language = Language(code="es-uy", language_code="es", country_code="UY", name="Spanish (Uruguay)")
            mock_response = self._create_mock_response_that_writes_file()

            with patch("adt_press.llm.speech_generation.litellm.aspeech", new_callable=AsyncMock) as mock_aspeech:
                with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                    with patch("adt_press.llm.speech_generation.render_template_to_string"):
                        with patch("adt_press.llm.speech_generation.get_azure_voice", return_value="es-UY-MateoNeural"):
                            mock_aspeech.return_value = mock_response

                            mock_segment = MagicMock()
                            mock_audio.from_mp3.return_value = mock_segment
                            mock_segment.set_frame_rate.return_value = mock_segment

                            await generate_speech_file(
                                run_output_dir=tmpdir,
                                config=config,
                                language=language,
                                text_id="test_text",
                                text="Hola desde Uruguay",
                            )

                            # Should use Azure (matched via base language "es")
                            call_kwargs = mock_aspeech.call_args[1]
                            assert "instructions" not in call_kwargs
                            assert call_kwargs["model"] == "azure/speech/azure-tts"
                            assert call_kwargs["voice"] == "es-UY-MateoNeural"


    @pytest.mark.asyncio
    async def test_generate_speech_file_silent_audio_uses_resolved_provider(self):
        """Test that silent audio generation uses resolved provider."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from adt_press.models.config import SpeechProviderConfig

            config = SpeechPromptConfig(
                model="default",
                template_path="prompts/speech_generation.jinja2",
                provider="openai",
                language_providers={"es": "azure"},
                openai=SpeechProviderConfig(model="tts-1", voice="alloy"),
                azure=SpeechProviderConfig(model="azure/speech/azure-tts", voice="auto"),
                format="mp3",
                bit_rate="64k",
                sample_rate=24000,
            )

            language = Language(code="es", language_code="es", name="Spanish")

            with patch("adt_press.llm.speech_generation.AudioSegment") as mock_audio:
                mock_silent = MagicMock()
                mock_audio.silent.return_value = mock_silent

                # Test with punctuation-only (triggers silent audio)
                result = await generate_speech_file(
                    run_output_dir=tmpdir,
                    config=config,
                    language=language,
                    text_id="test_dash",
                    text="—",
                )

                # Verify resolved provider is stored (Azure for Spanish)
                assert result.provider == "azure"
                assert result.model == "azure/speech/azure-tts"
                assert result.language_code == "es"
