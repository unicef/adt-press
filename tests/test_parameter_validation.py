import sys
import unittest
from pathlib import Path

from omegaconf import DictConfig, OmegaConf


class TestParameterValidation(unittest.TestCase):
    """Test that parameter validation works correctly with OmegaConf struct mode."""

    def setUp(self):
        self.config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        self.assertTrue(self.config_path.exists(), f"Config not found: {self.config_path}")

    def validate_cli_params(self, *args):
        """Test the parameter validation logic directly."""
        # Simulate CLI args
        original_argv = sys.argv
        sys.argv = ["test"] + list(args)

        try:
            cli_config = OmegaConf.from_cli()
            file_config = OmegaConf.load(str(self.config_path))

            # Enable struct mode to validate CLI parameters against config schema
            OmegaConf.set_struct(file_config, True)

            config = DictConfig(OmegaConf.merge(file_config, cli_config))
            return True, config
        except Exception as e:
            return False, str(e)
        finally:
            sys.argv = original_argv

    def test_valid_parameter_accepted(self):
        """Test that valid parameters are accepted."""
        # Use a valid parameter that should be accepted
        success, result = self.validate_cli_params("image_filters.size.min_side=100")

        self.assertTrue(success, f"Valid parameter was rejected: {result}")
        if success:
            self.assertEqual(result.image_filters.size.min_side, 100)

    def test_invalid_parameter_rejected(self):
        """Test that invalid parameters are rejected."""
        # Use the specific example from the issue
        success, error_msg = self.validate_cli_params("image_filters.min_side=100")

        self.assertFalse(success, "Invalid parameter was accepted")
        self.assertIn("Key 'min_side' is not in struct", error_msg)
        self.assertIn("image_filters.min_side", error_msg)

    def test_completely_invalid_parameter_rejected(self):
        """Test that completely invalid parameters are rejected."""
        success, error_msg = self.validate_cli_params("invalid_key=100")

        self.assertFalse(success, "Invalid parameter was accepted")
        self.assertIn("Key 'invalid_key' is not in struct", error_msg)

    def test_nested_invalid_parameter_rejected(self):
        """Test that invalid nested parameters are rejected."""
        success, error_msg = self.validate_cli_params("prompts.invalid_section.model=test")

        self.assertFalse(success, "Invalid parameter was accepted")
        self.assertIn("Key 'invalid_section' is not in struct", error_msg)

    def test_multiple_valid_parameters(self):
        """Test that multiple valid parameters work together."""
        success, result = self.validate_cli_params(
            "image_filters.size.min_side=100", "image_filters.size.max_side=2000", "clear_cache=true"
        )

        self.assertTrue(success, f"Valid parameters were rejected: {result}")
        if success:
            self.assertEqual(result.image_filters.size.min_side, 100)
            self.assertEqual(result.image_filters.size.max_side, 2000)
            self.assertEqual(result.clear_cache, True)

    def test_mixed_valid_invalid_parameters(self):
        """Test that mixing valid and invalid parameters still fails."""
        success, error_msg = self.validate_cli_params(
            "image_filters.size.min_side=100",  # valid
            "image_filters.invalid_key=200",  # invalid
        )

        self.assertFalse(success, "Mixed parameters should fail on invalid ones")
        self.assertIn("Key 'invalid_key' is not in struct", error_msg)


if __name__ == "__main__":
    unittest.main()
