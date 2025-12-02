import unittest
from types import SimpleNamespace
from unittest.mock import patch

from omegaconf import DictConfig

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

        with patch("adt_press.nodes.config_nodes.run_async_task", side_effect=lambda fn: SimpleNamespace(language_code="fr")) as run_async_mock:
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


if __name__ == "__main__":
    unittest.main()
