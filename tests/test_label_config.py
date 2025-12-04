import unittest
from types import SimpleNamespace
from unittest import mock
from unittest.mock import patch

from omegaconf import DictConfig, OmegaConf

from adt_press.nodes import config_nodes
from adt_press.utils.labels import clean_label_value, ensure_config_label, slug_from_pdf_path


class LabelConfigTests(unittest.TestCase):
    def test_label_config_respects_override(self) -> None:
        config = OmegaConf.create({"label": "My Custom Label"})
        with patch.object(config_nodes, "log") as log_mock:
            result = config_nodes.label_config(config, "/tmp/sample.pdf")

        self.assertEqual(result, "My Custom Label")
        log_mock.info.assert_called_once_with("label override used", label="My Custom Label")

    def test_label_config_generates_slug_from_pdf(self) -> None:
        config = OmegaConf.create({"label": "???"})
        with patch.object(config_nodes, "log") as log_mock:
            result = config_nodes.label_config(config, "/tmp/My Fancy Book.pdf")

        self.assertEqual(result, "my-fancy-book")
        log_mock.info.assert_called_once_with("label derived from pdf", label="my-fancy-book", source="My Fancy Book")

    def test_ensure_config_label_sets_value_and_updates_config(self) -> None:
        config = OmegaConf.create({"label": None, "pdf_path": "/tmp/cool.pdf"})
        with patch("adt_press.utils.labels.slug_from_pdf_path", return_value="cool") as slug_mock:
            label = ensure_config_label(config)

        self.assertEqual(label, "cool")
        self.assertEqual(config.label, "cool")
        slug_mock.assert_called_once()

    def test_clean_label_value_cleans_placeholders(self) -> None:
        self.assertIsNone(clean_label_value(None))
        self.assertIsNone(clean_label_value("???"))
        self.assertIsNone(clean_label_value("   "))

    def test_clean_label_value_returns_trimmed_value(self) -> None:
        self.assertEqual(clean_label_value("  Hello "), "Hello")

    def test_slug_from_pdf_path_raises_when_empty(self) -> None:
        with self.assertRaises(ValueError):
            slug_from_pdf_path("/tmp/---.pdf")

    def test_ensure_config_label_returns_existing_value_without_logging(self) -> None:
        config = DictConfig({"label": "keep", "pdf_path": "/tmp/book.pdf"})
        logger = SimpleNamespace(info=mock.Mock())
        label = ensure_config_label(config, logger=logger)

        self.assertEqual(label, "keep")
        logger.info.assert_not_called()

    def test_ensure_config_label_logs_when_set(self) -> None:
        config = DictConfig({"label": None, "pdf_path": "/tmp/book.pdf"})
        logger = SimpleNamespace(info=mock.Mock())

        with patch("adt_press.utils.labels.slug_from_pdf_path", return_value="book"):
            label = ensure_config_label(config, logger=logger)

        logger.info.assert_called_once_with("config label set automatically", label="book", source="/tmp/book.pdf")
        self.assertEqual(label, "book")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
