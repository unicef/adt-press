import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from omegaconf import DictConfig

from adt_press.pipeline import run_pipeline


class TestClearCache(unittest.TestCase):
    """Test that clear_cache functionality properly deletes the cache directory."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, "cache")

        # Create a basic config with our temp directory
        self.config = DictConfig(
            {
                "run_output_dir": self.temp_dir,
                "clear_cache": False,  # Will be overridden in tests
                "print_available_models": False,
                "web_generation": "rows",
            }
        )

    def tearDown(self):
        """Clean up after each test method."""
        # Remove the temporary directory and all its contents
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("adt_press.pipeline.driver")
    def test_clear_cache_deletes_existing_cache_directory(self, mock_driver):
        """Test that clear_cache=True deletes an existing cache directory."""
        # Create a cache directory with some content
        os.makedirs(self.cache_dir, exist_ok=True)
        test_file = os.path.join(self.cache_dir, "test_cache_file.txt")
        with open(test_file, "w") as f:
            f.write("test cache content")

        # Verify cache directory exists before running
        self.assertTrue(os.path.exists(self.cache_dir))
        self.assertTrue(os.path.exists(test_file))

        # Mock the Hamilton driver to avoid actual execution
        mock_driver_instance = MagicMock()
        mock_driver.Builder.return_value.with_modules.return_value.with_cache.return_value.with_adapters.return_value.build.return_value = (
            mock_driver_instance
        )

        # Set clear_cache to True and run pipeline
        self.config["clear_cache"] = True
        run_pipeline(self.config)

        # Verify cache directory was deleted
        self.assertFalse(os.path.exists(self.cache_dir))
        self.assertFalse(os.path.exists(test_file))

    @patch("adt_press.pipeline.driver")
    def test_clear_cache_false_preserves_existing_cache_directory(self, mock_driver):
        """Test that clear_cache=False preserves an existing cache directory."""
        # Create a cache directory with some content
        os.makedirs(self.cache_dir, exist_ok=True)
        test_file = os.path.join(self.cache_dir, "test_cache_file.txt")
        with open(test_file, "w") as f:
            f.write("test cache content")

        # Verify cache directory exists before running
        self.assertTrue(os.path.exists(self.cache_dir))
        self.assertTrue(os.path.exists(test_file))

        # Mock the Hamilton driver to avoid actual execution
        mock_driver_instance = MagicMock()
        mock_driver.Builder.return_value.with_modules.return_value.with_cache.return_value.with_adapters.return_value.build.return_value = (
            mock_driver_instance
        )

        # Set clear_cache to False and run pipeline
        self.config["clear_cache"] = False
        run_pipeline(self.config)

        # Verify cache directory still exists
        self.assertTrue(os.path.exists(self.cache_dir))
        self.assertTrue(os.path.exists(test_file))

        # Verify content is preserved
        with open(test_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "test cache content")
