import tempfile
import unittest
from pathlib import Path

from omegaconf import DictConfig, OmegaConf

from adt_press.pipeline import run_pipeline


def test_pass():
    assert True


class PipelineTest(unittest.TestCase):
    def test_pipeline_integration_first_five_pages(self):
        """Test the entire pipeline with first 6 pages using default config values."""

        # Create a temporary output directory for this test
        with tempfile.TemporaryDirectory() as temp_dir:
            file_config = OmegaConf.load("config/config.yaml")
            print(temp_dir)

            test_config = {
                "output_dir": temp_dir,
                "page_range": dict(start=0, end=5),
                "clear_cache": "true",
            }

            config = DictConfig(OmegaConf.merge(file_config, test_config))
            run_pipeline(config)

            # assert that our output files were created
            output_files = [
                f"{temp_dir}/processed_images.html",
                f"{temp_dir}/pruned_images.html",
                f"{temp_dir}/page_report.html",
                f"{temp_dir}/config.html",
                f"{temp_dir}/index.html",
            ]

            # print out all the files in the temp directory to help with test failures
            print("Output files in temp directory:")
            for file in Path(temp_dir).iterdir():
                print(file)

            for file in output_files:
                file_path = Path(file)
                assert file_path.exists(), f"Output file {file} was not created."

            # assert our number of vector images
            vector_images = list(Path(temp_dir).glob("img_p*_v*.png"))
            self.assertEqual(len(vector_images), 70)

            # assert our number of raster images
            raster_images = list(Path(temp_dir).glob("img_p*_r*.png"))
            self.assertEqual(len(raster_images), 8)

            # assert our number of page images
            page_images = list(Path(temp_dir).glob("img_p?.png"))
            self.assertEqual(len(page_images), 5)

            # TODO: Add more specific assertions about the content of the output files
