import sys
import unittest
import importlib.util
from unittest.mock import patch

from omegaconf.errors import ConfigKeyError


class TestParameterValidation(unittest.TestCase):
    """Test that main() fails on unrecognized parameters."""

    def test_main_fails_on_invalid_parameters(self):
        """Test that main() fails when called with invalid parameters."""
        # Load the main function directly from adt-press.py file
        spec = importlib.util.spec_from_file_location(
            "adt_press_main", 
            "/home/runner/work/adt-press/adt-press/adt-press.py"
        )
        adt_press_main = importlib.util.module_from_spec(spec)
        
        # Mock run_pipeline before loading the module to avoid dependency issues
        with patch.dict('sys.modules', {'adt_press.pipeline': sys.modules.get('unittest.mock', None)}):
            # Create a mock for run_pipeline
            import unittest.mock
            mock_module = unittest.mock.MagicMock()
            mock_module.run_pipeline = unittest.mock.MagicMock()
            sys.modules['adt_press.pipeline'] = mock_module
            
            # Now load the module
            spec.loader.exec_module(adt_press_main)
            
            # Test with invalid parameter that should cause ConfigKeyError
            with patch.object(sys, 'argv', ['adt-press.py', 'image_filters.min_side=100']):
                with self.assertRaises(ConfigKeyError) as context:
                    adt_press_main.main()
                
                # Verify the error message contains the expected information
                error_msg = str(context.exception)
                self.assertIn("Key 'min_side' is not in struct", error_msg)
                self.assertIn("image_filters.min_side", error_msg)


if __name__ == "__main__":
    unittest.main()
