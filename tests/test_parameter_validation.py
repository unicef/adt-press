import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from omegaconf.errors import ConfigKeyError


class TestParameterValidation(unittest.TestCase):
    """Test that main() fails on unrecognized parameters."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Load the main function directly from adt-press.py file
        main_path = str(Path(os.path.abspath(__file__)).parent.parent) + os.sep + "adt-press.py"
        spec = importlib.util.spec_from_file_location("adt_press_main", main_path)
        self.adt_press_main = importlib.util.module_from_spec(spec)

        # Create a mock for run_pipeline
        self.mock_module = MagicMock()
        self.mock_module.run_pipeline = MagicMock()

        # Mock run_pipeline before loading the module to avoid dependency issues
        self.module_patcher = patch.dict("sys.modules", {"adt_press.pipeline": self.mock_module})
        self.module_patcher.start()

        # Now load the module
        spec.loader.exec_module(self.adt_press_main)

    def tearDown(self):
        """Clean up after each test method."""
        self.module_patcher.stop()

    def test_main_fails_on_invalid_parameters(self):
        """Test that main() fails when called with invalid parameters."""
        # Test with invalid parameter that should cause ConfigKeyError
        with patch.object(sys, "argv", ["adt-press.py", "image_filters.min_side=100", "label=momo", "pdf_path=assets/momo.pdf"]):
            with self.assertRaises(ConfigKeyError) as context:
                self.adt_press_main.main()

            # Verify the error message contains the expected information
            error_msg = str(context.exception)
            self.assertIn("Key 'min_side' is not in struct", error_msg)
            self.assertIn("image_filters.min_side", error_msg)

    def test_main_succeeds_on_valid_parameters(self):
        """Test that main() succeeds when called with valid parameters."""
        # Test with valid parameter that should succeed
        with patch.object(
            sys, "argv", ["adt-press.py", "image_filters.size.min_side=300", "label=momo", "clear_cache=true", "pdf_path=assets/momo.pdf"]
        ):
            # This should not raise any exceptions
            self.adt_press_main.main()

            # Verify that run_pipeline was called, indicating main() completed successfully
            self.mock_module.run_pipeline.assert_called_once()
