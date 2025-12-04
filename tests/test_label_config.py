import unittest
from unittest.mock import patch

from omegaconf import OmegaConf

from adt_press.nodes import config_nodes
from adt_press.utils.labels import ensure_config_label


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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
