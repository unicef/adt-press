import os
import tempfile
import unittest
from pathlib import Path

from omegaconf import DictConfig, OmegaConf

from adt_press.pipeline import run_pipeline


class PipelineTest(unittest.TestCase):
    temp_dir: str
    run_dir: str

    def assertFileCount(self, pattern: str, expected_count: int, msg: str = ""):
        files = list(Path(self.run_dir).glob(pattern))
        self.assertEqual(len(files), expected_count, msg)

    def assertFileContains(self, name: str, content: str, msg: str = ""):
        file_path = Path(self.run_dir) / name
        self.assertTrue(file_path.exists(), f"File {name} does not exist.")
        with open(file_path, "r") as f:
            file_content = f.read()
        self.assertIn(content, file_content, msg)

    def assertFileDoesNotContain(self, name: str, content: str, msg: str = ""):
        file_path = Path(self.run_dir) / name
        self.assertTrue(file_path.exists(), f"File {name} does not exist.")
        with open(file_path, "r") as f:
            file_content = f.read()
        self.assertNotIn(content, file_content, msg)

    def test_pipeline_integration_first_five_pages(self):
        """Test the entire pipeline with first 6 pages using default config values."""

        # Create a temporary output directory for this test
        with tempfile.TemporaryDirectory() as self.temp_dir:
            file_config = OmegaConf.load("config/config.yaml")
            print(self.temp_dir)
            self.run_dir = os.path.join(self.temp_dir, "raven")

            test_config = {
                "output_dir": self.temp_dir,
                "web_strategy": "rows",
                "crop_strategy": "llm",
                "label": "raven",
                "pdf_path": "assets/raven.pdf",
                "page_range": dict(start=0, end=5),
                "plate_language": "fr",
                "output_languages": ["en", "fr"],
                "print_available_models": "true",
            }

            config = DictConfig(OmegaConf.merge(file_config, test_config))
            run_pipeline(config)

            # print out all the files in the temp directory to help with test failures
            print("Output files in temp directory:")
            for file in Path(self.run_dir).iterdir():
                print(file)

            print("Files in images directory:")
            for file in (Path(self.run_dir) / "images").iterdir():
                print(file)                

            # assert that our output report was created
            output_files = [
                "processed_images.html",
                "pruned_images.html",
                "page_report.html",
                "config.html",
                "index.html",
                "plate_report.html",
                "web_report.html",
                "glossary_report.html",
                "translation_report.html",
            ]

            for file in output_files:
                file_path = Path(f"{self.run_dir}/{file}")
                assert file_path.exists(), f"Output file {file} was not created."

            self.assertFileCount("*.html", len(output_files), "Unexpected number of HTML files created")
            self.assertFileCount("run.png", 1, "Run image not created")
            self.assertFileCount("images/page_?.png", 5, "Unexpected number of page images created")
            self.assertFileCount("images/img_p*_v?.png", 5, "Unexpected number of vector images created")
            self.assertFileCount("images/img_p*_r?.png", 10, "Unexpected number of raster images created")
            self.assertFileCount("images/img_p*_r*_crop*.png", 5, "Unexpected number of cropped images created")
            self.assertFileCount("images/img_p*_r*_recrop.png", 5, "Unexpected number of recropped images created")
            self.assertFileCount("images/img_p*_chart.png", 15, "Unexpected number of chart images created")

            self.assertFileContains("page_report.html", ">Hyena and Raven<", "Title not found in page report")
            self.assertFileContains("page_report.html", ">sec_p1_s0<", "No section found for page 1 in page report")
            self.assertFileContains("page_report.html", "French", "Output language not found in page report")
            self.assertFileContains("page_report.html", "English", "Input language not found in page report")
            self.assertFileContains("page_report.html", "corbeau", "Translated text not found in page report")
            self.assertFileContains("page_report.html", "Glossary", "No glossary section found in report")
            self.assertFileContains("page_report.html", "Easy Read", "No easy read section found in report")

    def test_pipeline_integration_no_translation(self):
        # Create a temporary output directory for this test
        with tempfile.TemporaryDirectory() as self.temp_dir:
            file_config = OmegaConf.load("config/config.yaml")
            print(self.temp_dir)
            self.run_dir = os.path.join(self.temp_dir, "raven")

            test_config = {
                "output_dir": self.temp_dir,
                "web_strategy": "html",
                "crop_strategy": "none",
                "caption_strategy": "none",
                "glossary_strategy": "none",
                "explanation_strategy": "none",
                "easy_read_strategy": "none",
                "speech_strategy": "none",
                "label": "raven",
                "pdf_path": "assets/raven.pdf",
                "page_range": dict(start=0, end=5),
                "plate_language": "en",
                "output_languages": ["en"],
            }

            config = DictConfig(OmegaConf.merge(file_config, test_config))
            run_pipeline(config)

            # print out all the files in the temp directory to help with test failures
            print("Output files in temp directory:")
            for file in Path(self.run_dir).iterdir():
                print(file)

            # assert that our output report was created
            output_files = [
                "processed_images.html",
                "pruned_images.html",
                "page_report.html",
                "config.html",
                "index.html",
                "plate_report.html",
                "web_report.html",
                "glossary_report.html",
                "translation_report.html",
            ]

            for file in output_files:
                file_path = Path(f"{self.run_dir}/{file}")
                assert file_path.exists(), f"Output file {file} was not created."

            self.assertFileContains("page_report.html", ">Hyena and Raven<", "Title not found in page report")
            self.assertFileContains("page_report.html", ">sec_p1_s0<", "No section found for page 1 in page report")
            self.assertFileDoesNotContain("page_report.html", "corbeau", "French should not be in page report")

            # rerun using two column web strategy
            test_config["web_strategy"] = "two_column"
            config = DictConfig(OmegaConf.merge(file_config, test_config))
            run_pipeline(config)

            # TODO: once we have deterministic outputs, add tests of final web content
