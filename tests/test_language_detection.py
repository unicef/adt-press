import unittest

from omegaconf import DictConfig, OmegaConf

from adt_press.models.metadata import BookMetadata
from adt_press.nodes import config_nodes, pdf_nodes
from adt_press.utils.languages import Language


class InputLanguageConfigTests(unittest.TestCase):
    def test_input_language_config_respects_manual_override(self) -> None:
        config = DictConfig({"input_language": "es"})
        result = config_nodes.input_language_config(config)
        self.assertEqual(result, "es")

    def test_input_language_config_returns_auto_when_not_set(self) -> None:
        config = DictConfig({"input_language": None})
        result = config_nodes.input_language_config(config)
        self.assertEqual(result, "auto")

    def test_input_language_config_defaults_to_auto(self) -> None:
        config = DictConfig({})
        result = config_nodes.input_language_config(config)
        self.assertEqual(result, "auto")


class InputLanguageNodeTests(unittest.TestCase):
    def test_input_language_from_config(self) -> None:
        book_metadata = BookMetadata(language_code="fr", reasoning="test")
        result = pdf_nodes.input_language("es", book_metadata)
        self.assertEqual(result.code, "es")
        self.assertEqual(result.language_code, "es")

    def test_input_language_from_metadata(self) -> None:
        book_metadata = BookMetadata(language_code="fr", reasoning="test")
        result = pdf_nodes.input_language("auto", book_metadata)
        self.assertEqual(result.code, "fr")
        self.assertEqual(result.language_code, "fr")

    def test_input_language_raises_when_unavailable(self) -> None:
        book_metadata = BookMetadata(language_code=None, reasoning="test")
        with self.assertRaises(ValueError) as context:
            pdf_nodes.input_language("auto", book_metadata)
        self.assertIn("Input language could not be determined", str(context.exception))


class LanguageClassTests(unittest.TestCase):
    def test_language_valid_two_letter_code(self) -> None:
        lang = Language.from_code("en")
        self.assertEqual(lang.code, "en")
        self.assertEqual(lang.language_code, "en")
        self.assertEqual(lang.country_code, "")
        self.assertEqual(lang.name, "English")

    def test_language_with_locale(self) -> None:
        lang = Language.from_code("en-US")
        self.assertEqual(lang.code, "en-us")
        self.assertEqual(lang.language_code, "en")
        self.assertEqual(lang.country_code, "US")
        self.assertIn("United States", lang.name)

    def test_language_normalizes_case(self) -> None:
        lang = Language.from_code("ES")
        self.assertEqual(lang.code, "es")
        self.assertEqual(lang.language_code, "es")

    def test_language_invalid_code_raises(self) -> None:
        with self.assertRaises(ValueError) as context:
            Language.from_code("xx")
        self.assertIn("Invalid language code", str(context.exception))

    def test_language_invalid_country_code_raises(self) -> None:
        with self.assertRaises(ValueError) as context:
            Language.from_code("en-XX")
        self.assertIn("Invalid country code", str(context.exception))

    def test_language_equality(self) -> None:
        lang1 = Language.from_code("en")
        lang2 = Language.from_code("en")
        lang3 = Language.from_code("es")
        self.assertEqual(lang1, lang2)
        self.assertNotEqual(lang1, lang3)

    def test_language_hash(self) -> None:
        lang1 = Language.from_code("en")
        lang2 = Language.from_code("en")
        self.assertEqual(hash(lang1), hash(lang2))


class ConfigNodesHelperTests(unittest.TestCase):
    def test_plate_language_config_override(self) -> None:
        config = OmegaConf.create({"plate_language": "fr"})
        result = config_nodes.plate_language_config(config)
        self.assertEqual(result, "fr")

    def test_plate_language_defaults_to_auto(self) -> None:
        config = OmegaConf.create({})
        result = config_nodes.plate_language_config(config)
        self.assertEqual(result, "auto")

    def test_output_languages_config_respects_list(self) -> None:
        config = OmegaConf.create({"output_languages": ["en", "fr"]})
        result = config_nodes.output_languages_config(config)
        self.assertEqual(result, ["en", "fr"])

    def test_output_languages_config_defaults_to_auto(self) -> None:
        config = OmegaConf.create({})
        result = config_nodes.output_languages_config(config)
        self.assertEqual(result, ["auto"])


class PlateLanguageNodeTests(unittest.TestCase):
    def test_plate_language_from_config(self) -> None:
        input_lang = Language.from_code("en")
        result = pdf_nodes.plate_language("fr", input_lang)
        self.assertEqual(result.code, "fr")

    def test_plate_language_defaults_to_input(self) -> None:
        input_lang = Language.from_code("es")
        result = pdf_nodes.plate_language("auto", input_lang)
        self.assertEqual(result.code, "es")


class OutputLanguagesNodeTests(unittest.TestCase):
    def test_output_languages_from_config(self) -> None:
        plate_lang = Language.from_code("en")
        result = pdf_nodes.output_languages(["en", "fr"], plate_lang)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].code, "en")
        self.assertEqual(result[1].code, "fr")

    def test_output_languages_defaults_to_plate(self) -> None:
        plate_lang = Language.from_code("es")
        result = pdf_nodes.output_languages(["auto"], plate_lang)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].code, "es")

    def test_output_languages_none_list_defaults_to_plate(self) -> None:
        plate_lang = Language.from_code("es")
        result = pdf_nodes.output_languages(["auto"], plate_lang)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].code, "es")


if __name__ == "__main__":
    unittest.main()
