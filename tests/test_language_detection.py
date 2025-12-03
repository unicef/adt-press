import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from omegaconf import DictConfig

from adt_press.llm.language_detection import LanguageDetectionResponse, detect_input_language
from adt_press.models.config import PromptConfig
from adt_press.models.text import PageText, PageTextGroup, PageTexts, TextGroupType, TextType
from adt_press.nodes import config_nodes


class InputLanguageConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prompt_config = PromptConfig(model="gpt-5", template_path="prompts/language_detection.jinja2")
        self.sample_pdf_texts = {
            "page_1": PageTexts(
                page_id="page_1",
                groups=[
                    PageTextGroup(
                        group_id="g1",
                        group_type=TextGroupType.paragraph,
                        texts=[
                            PageText(
                                text_id="txt_1",
                                text="Bonjour tout le monde",
                                text_type=TextType.section_text,
                            )
                        ],
                    )
                ],
                reasoning="",
            )
        }

    def test_input_language_config_respects_manual_override(self) -> None:
        config = DictConfig({"input_language": "ES"})
        with patch("adt_press.nodes.config_nodes.run_async_task") as run_async_mock:
            result = config_nodes.input_language_config(config, self.prompt_config, self.sample_pdf_texts)

        self.assertEqual(result, "es")
        run_async_mock.assert_not_called()

    def test_input_language_config_calls_detector_when_not_overridden(self) -> None:
        config = DictConfig({"input_language": None})

        with patch(
            "adt_press.nodes.config_nodes.run_async_task", side_effect=lambda fn: SimpleNamespace(language_code="fr")
        ) as run_async_mock:
            result = config_nodes.input_language_config(config, self.prompt_config, self.sample_pdf_texts)

        self.assertEqual(result, "fr")
        run_async_mock.assert_called_once()

    def test_input_language_config_defaults_to_english_when_no_text(self) -> None:
        empty_texts: dict[str, PageTexts] = {}
        config = DictConfig({"input_language": None})

        with patch("adt_press.nodes.config_nodes.run_async_task") as run_async_mock:
            result = config_nodes.input_language_config(config, self.prompt_config, empty_texts)

        self.assertEqual(result, "en")
        run_async_mock.assert_not_called()


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


if __name__ == "__main__":
    unittest.main()
