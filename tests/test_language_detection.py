import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from omegaconf import DictConfig, OmegaConf

from adt_press.llm.language_detection import LanguageDetectionResponse, detect_input_language
from adt_press.models.config import PromptConfig
from adt_press.models.text import PageText, PageTextGroup, PageTexts, TextGroupType, TextType
from adt_press.nodes import config_nodes


class InputLanguageConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prompt_config = PromptConfig(model="gpt-5", template_path="prompts/language_detection.jinja2")
        self.sample_pdf_texts = "Bonjour tout le monde"

    def test_input_language_config_respects_manual_override(self) -> None:
        config = DictConfig({"input_language": "ES"})
        with patch("adt_press.nodes.config_nodes.run_async_task") as run_async_mock, patch.object(config_nodes, "log") as log_mock:
            result = config_nodes.input_language_config(config, self.prompt_config, self.sample_pdf_texts)

        self.assertEqual(result, "es")
        run_async_mock.assert_not_called()

    def test_input_language_config_calls_detector_when_not_overridden(self) -> None:
        config = DictConfig({"input_language": None})

        with (
            patch(
                "adt_press.nodes.config_nodes.run_async_task",
                side_effect=lambda fn: SimpleNamespace(language_code="fr", confidence=0.42),
            ) as run_async_mock,
            patch.object(config_nodes, "log") as log_mock,
        ):
            result = config_nodes.input_language_config(config, self.prompt_config, self.sample_pdf_texts)

        self.assertEqual(result, "fr")
        run_async_mock.assert_called_once()
        log_mock.info.assert_called_once_with("input language detected automatically", language="fr", confidence=0.42)

    def test_input_language_config_defaults_to_english_when_no_text(self) -> None:
        empty_texts: str = ""
        config = DictConfig({"input_language": None})

        with patch("adt_press.nodes.config_nodes.run_async_task") as run_async_mock, patch.object(config_nodes, "log") as log_mock:
            with self.assertRaises(ValueError):
                config_nodes.input_language_config(config, self.prompt_config, empty_texts)

        run_async_mock.assert_not_called()

    def test_input_language_config_handles_missing_mandatory_value(self) -> None:
        config = OmegaConf.create({"input_language": "???"})

        with (
            patch(
                "adt_press.nodes.config_nodes.run_async_task",
                side_effect=lambda fn: SimpleNamespace(language_code="de", confidence=0.7),
            ) as run_async_mock,
            patch.object(config_nodes, "log") as log_mock,
        ):
            result = config_nodes.input_language_config(config, self.prompt_config, self.sample_pdf_texts)

        self.assertEqual(result, "de")
        run_async_mock.assert_called_once()
        log_mock.info.assert_called_once_with("input language detected automatically", language="de", confidence=0.7)


class FakeCompletions:
    def __init__(self, responder):
        self._responder = responder
        self.calls: list[dict] = []

    async def create(self, **kwargs):  # type: ignore[override]
        self.calls.append(kwargs)
        return self._responder()


class FakeChat:
    def __init__(self, responder):
        self.completions = FakeCompletions(responder)


class FakeClient:
    def __init__(self, responder):
        self.chat = FakeChat(responder)


class LanguageDetectionLLMTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prompt_config = PromptConfig(model="gpt-5", template_path="prompts/language_detection.jinja2")

    def test_detect_input_language_success(self) -> None:
        response = LanguageDetectionResponse(language_code="ES", reasoning="accented words", confidence=0.9)
        fake_client = FakeClient(lambda: response)

        with patch("adt_press.llm.language_detection.get_instructor_client", return_value=fake_client):
            result = asyncio.run(detect_input_language("Hola mundo", self.prompt_config))

        self.assertEqual(result.language_code, "es")
        self.assertGreater(result.confidence, 0)
        # ensure prompt included sample text
        call_kwargs = fake_client.chat.completions.calls[0]
        self.assertIn("Hola mundo", str(call_kwargs["messages"]))

    def test_detect_input_language_invalid_code_raises(self) -> None:
        def responder():
            return LanguageDetectionResponse(language_code="xx", reasoning="", confidence=0.1)  # type: ignore[arg-type]

        fake_client = FakeClient(responder)

        with patch("adt_press.llm.language_detection.get_instructor_client", return_value=fake_client):
            with self.assertRaises(ValueError):
                asyncio.run(detect_input_language("N/A", self.prompt_config))

    def test_language_detection_response_rejects_unknown_code(self) -> None:
        with self.assertRaises(ValueError):
            LanguageDetectionResponse(language_code="xx", reasoning="", confidence=None)


class ConfigNodesHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_pdf_texts = "Bonjour le monde"
        self.prompt_config = PromptConfig(model="gpt-5", template_path="prompts/language_detection.jinja2")

    def test_clean_language_override_normalizes_and_filters(self) -> None:
        self.assertIsNone(config_nodes._clean_language_override(None))
        self.assertIsNone(config_nodes._clean_language_override("???"))
        self.assertEqual(config_nodes._clean_language_override(" Es "), "es")

    def test_sample_pdf_text_respects_character_limit(self) -> None:
        sample = config_nodes._sample_pdf_text_for_language_detection(self.sample_pdf_texts, max_chars=5)
        self.assertEqual(sample, "Bonjour")

    def test_input_language_config_handles_detection_failure(self) -> None:
        config = DictConfig({"input_language": None})

        with (
            patch("adt_press.nodes.config_nodes.run_async_task", side_effect=RuntimeError("boom")) as run_async_mock,
            patch.object(config_nodes, "log") as log_mock,
        ):
            result = config_nodes.input_language_config(config, self.prompt_config, self.sample_pdf_texts)

        self.assertEqual(result, "en")
        run_async_mock.assert_called_once()
        log_mock.warning.assert_called_once()
        log_mock.info.assert_called_with("input language defaulted to english", reason="detection_error")

    def test_plate_language_config_override(self) -> None:
        config = OmegaConf.create({"plate_language": "FR"})
        with patch.object(config_nodes, "log") as log_mock:
            result = config_nodes.plate_language_config(config, "en")

        self.assertEqual(result, "fr")
        log_mock.info.assert_called_once_with("plate language override used", language="fr")

    def test_plate_language_defaults_to_input(self) -> None:
        config = OmegaConf.create({})
        with patch.object(config_nodes, "log") as log_mock:
            result = config_nodes.plate_language_config(config, "es")

        self.assertEqual(result, "es")
        log_mock.info.assert_called_once_with("plate language defaulted to input language", language="es")

    def test_output_languages_config_respects_list(self) -> None:
        config = OmegaConf.create({"output_languages": ["EN", "fr"]})
        with patch.object(config_nodes, "log") as log_mock:
            result = config_nodes.output_languages_config(config, "es")

        self.assertEqual(result, ["en", "fr"])
        log_mock.info.assert_called_with("output languages configured", languages=["en", "fr"])

    def test_output_languages_config_defaults_when_missing(self) -> None:
        config = OmegaConf.create({"output_languages": ["???", None]})
        with patch.object(config_nodes, "log") as log_mock:
            result = config_nodes.output_languages_config(config, "de")

        self.assertEqual(result, ["de"])
        log_mock.info.assert_called_with("output languages defaulted to input language", languages=["de"])


if __name__ == "__main__":
    unittest.main()
