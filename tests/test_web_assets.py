"""Tests for web assets management."""

import subprocess
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from adt_press.utils.web_assets import (
    copy_build_files,
    copy_interface_translations,
    copy_web_assets,
    install_dictionaries,
    install_fontawesome,
    run_npm_build,
)


class TestCopyWebAssets:
    """Test copying web assets."""

    def test_copy_assets_to_output(self):
        """Test copying assets directory to output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            
            with patch("shutil.copytree") as mock_copytree:
                with patch("shutil.copy2"):
                    with patch("os.makedirs"):
                        with patch("os.listdir", return_value=["libs", "modules"]):
                            with patch("os.path.isdir", return_value=True):
                                copy_web_assets(tmpdir)
                
                # Should copy multiple directories
                assert mock_copytree.call_count >= 1


class TestCopyBuildFiles:
    """Test copying build files."""

    def test_copy_package_json(self):
        """Test copying build files to build directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            
            with patch("shutil.copy") as mock_copy:
                with patch("shutil.rmtree"):
                    with patch("os.makedirs"):
                        copy_build_files(tmpdir)
                
                # Should copy Makefile, package.json, and tailwind.config.js
                assert mock_copy.call_count == 3
                
                # Check that package.json was copied
                calls = [str(c) for c in mock_copy.call_args_list]
                package_calls = [c for c in calls if "package.json" in c]
                assert len(package_calls) == 1


class TestCopyInterfaceTranslations:
    """Test copying interface translations."""

    def test_copy_with_language_code(self):
        """Test copying with specific language codes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            
            with patch("shutil.copytree") as mock_copy:
                with patch("shutil.rmtree"):
                    with patch("os.makedirs"):
                        with patch("os.path.exists", return_value=True):
                            copy_interface_translations(tmpdir, ["es", "en"])
                
                # Should copy directories for each language
                assert mock_copy.call_count == 2

    def test_copy_skips_missing_languages(self):
        """Test that missing languages are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            
            def exists_mock(path):
                # Return False for 'zz' language, True for 'en'
                return "en" in path
            
            with patch("shutil.copytree") as mock_copy:
                with patch("shutil.rmtree"):
                    with patch("os.makedirs"):
                        with patch("os.path.exists", side_effect=exists_mock):
                            copy_interface_translations(tmpdir, ["zz", "en"])
                
                # Should only copy the existing language
                assert mock_copy.call_count == 1


class TestInstallDictionaries:
    """Test installing dictionaries."""

    def test_install_single_dictionary(self):
        """Test installing a single dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            
            mock_result = MagicMock(returncode=0, stdout="", stderr="")
            
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                with patch("shutil.rmtree"):
                    with patch("os.makedirs"):
                        with patch("os.path.exists", return_value=True):
                            with patch("shutil.copy2"):
                                install_dictionaries(tmpdir, ["es"])
                
                # Should run npm install for the language
                assert mock_run.call_count >= 1
                first_call = mock_run.call_args_list[0]
                cmd = first_call[0][0]
                assert cmd[0] == "npm"
                assert cmd[1] == "install"
                assert "dictionary-" in cmd[2]
                assert first_call[1]["capture_output"] is True

    def test_install_fails_gracefully(self):
        """Test that installation failure logs warning but doesn't raise."""
        with tempfile.TemporaryDirectory() as tmpdir:
            
            def run_side_effect(*args, **kwargs):
                raise subprocess.CalledProcessError(1, "npm install", "Package not found")
            
            with patch("subprocess.run", side_effect=run_side_effect):
                with patch("shutil.rmtree"):
                    with patch("os.makedirs"):
                        with patch("os.path.exists", return_value=False):
                            # Should not raise exception
                            install_dictionaries(tmpdir, ["zz"])


class TestInstallFontAwesome:
    """Test installing Font Awesome."""

    def test_install_fontawesome(self):
        """Test installing Font Awesome package."""
        with tempfile.TemporaryDirectory() as tmpdir:
            
            mock_result = MagicMock(returncode=0, stdout="", stderr="")
            
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                with patch("shutil.rmtree"):
                    with patch("os.makedirs"):
                        with patch("os.path.exists", return_value=True):
                            with patch("shutil.copy2"):
                                with patch("shutil.copytree"):
                                    install_fontawesome(tmpdir)
                
                # Should run npm install in build directory
                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]
                assert cmd[0] == "npm"
                assert cmd[1] == "install"
                assert "@fortawesome/fontawesome-free" in cmd[2]
                assert mock_run.call_args[1]["cwd"].endswith("/build")
                assert mock_run.call_args[1]["capture_output"] is True


class TestRunNpmBuild:
    """Test npm build process."""

    def test_successful_build(self):
        """Test successful npm build with install and tailwind."""
        with tempfile.TemporaryDirectory() as tmpdir:
            
            mock_npm = MagicMock(returncode=0, stdout="", stderr="")
            mock_tailwind = MagicMock(returncode=0, stdout="Done", stderr="")
            
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [mock_npm, mock_tailwind]
                
                run_npm_build(tmpdir)
                
                # Should call npm install then tailwindcss
                assert mock_run.call_count == 2
                
                # Check npm install
                npm_call = mock_run.call_args_list[0]
                assert npm_call[0][0][0] == "npm"
                assert npm_call[0][0][1] == "install"
                assert npm_call[1]["capture_output"] is True
                
                # Check tailwindcss
                tailwind_call = mock_run.call_args_list[1]
                assert "tailwindcss" in tailwind_call[0][0]
                assert tailwind_call[1]["capture_output"] is True

    def test_npm_install_failure_raises(self):
        """Test that npm install failure raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            
            def run_side_effect(*args, **kwargs):
                raise subprocess.CalledProcessError(1, "npm install", "Package not found")
            
            with patch("subprocess.run", side_effect=run_side_effect):
                with pytest.raises(subprocess.CalledProcessError):
                    run_npm_build(tmpdir)

    def test_tailwind_failure_raises(self):
        """Test that Tailwind compilation failure raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            
            def run_side_effect(*args, **kwargs):
                # npm install succeeds, tailwind fails
                if "npm" in args[0][0]:
                    return MagicMock(returncode=0, stdout="", stderr="")
                raise subprocess.CalledProcessError(9, "tailwindcss", "Input file not found")
            
            with patch("subprocess.run", side_effect=run_side_effect):
                with pytest.raises(subprocess.CalledProcessError):
                    run_npm_build(tmpdir)

    def test_subprocess_output_captured(self):
        """Test that subprocess output is captured (not printed)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            
            mock_result = MagicMock(returncode=0, stdout="verbose output", stderr="")
            
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                run_npm_build(tmpdir)
                
                # All subprocess calls should capture output
                for call_item in mock_run.call_args_list:
                    assert call_item[1]["capture_output"] is True
