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


class TestInstallMathJax:
    """Test installing MathJax."""

    def test_install_mathjax_success(self):
        """Test successful MathJax installation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_result = MagicMock(returncode=0, stdout="", stderr="")

            with patch("subprocess.run", return_value=mock_result) as mock_run:
                with patch("shutil.rmtree"):
                    with patch("os.makedirs"):
                        with patch("os.path.exists", return_value=True):
                            with patch("shutil.copytree"):
                                from adt_press.utils.web_assets import install_mathjax

                                install_mathjax(tmpdir)

                # Should run npm install for mathjax@3
                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]
                assert cmd[0] == "npm"
                assert cmd[1] == "install"
                assert "mathjax@3" in cmd[2]
                assert mock_run.call_args[1]["capture_output"] is True

    def test_install_mathjax_fallback(self):
        """Test fallback to local assets when npm fails."""
        with tempfile.TemporaryDirectory() as tmpdir:

            def run_side_effect(*args, **kwargs):
                raise subprocess.CalledProcessError(1, "npm", "Network error")

            with patch("subprocess.run", side_effect=run_side_effect):
                with patch("shutil.rmtree"):
                    with patch("os.makedirs"):
                        with patch("os.path.exists", return_value=True):
                            with patch("shutil.copytree") as mock_copytree:
                                from adt_press.utils.web_assets import install_mathjax

                                # Should not raise, should fallback
                                install_mathjax(tmpdir)

                                # Should attempt to copy from local assets
                                assert mock_copytree.called


class TestBundleJavaScript:
    """Test JavaScript bundling."""

    def test_bundle_javascript_success(self):
        """Test successful JavaScript bundling."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_result = MagicMock(returncode=0, stdout="", stderr="")

            with patch("subprocess.run", return_value=mock_result) as mock_run:
                with patch("os.path.abspath", side_effect=lambda x: f"/abs{x}"):
                    from adt_press.utils.web_assets import bundle_javascript

                    bundle_javascript(tmpdir)

                # Should install esbuild then bundle
                assert mock_run.call_count == 2

                # First call: npm install esbuild
                npm_call = mock_run.call_args_list[0]
                assert npm_call[0][0][0] == "npm"
                assert npm_call[0][0][1] == "install"
                assert "esbuild" in npm_call[0][0][2]

                # Second call: esbuild bundling
                esbuild_call = mock_run.call_args_list[1]
                assert "esbuild" in esbuild_call[0][0]
                assert "--bundle" in esbuild_call[0][0]
                assert "--minify" in esbuild_call[0][0]
                assert "--sourcemap" in esbuild_call[0][0]

    def test_bundle_javascript_failure_graceful(self):
        """Test that bundling failure is handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:

            def run_side_effect(*args, **kwargs):
                # npm install succeeds, esbuild fails
                if "npm" in args[0][0]:
                    return MagicMock(returncode=0, stdout="", stderr="")
                raise subprocess.CalledProcessError(1, "esbuild", stderr="Parse error")

            with patch("subprocess.run", side_effect=run_side_effect):
                with patch("os.path.abspath", side_effect=lambda x: f"/abs{x}"):
                    from adt_press.utils.web_assets import bundle_javascript

                    # Should not raise, should print warning
                    bundle_javascript(tmpdir)


class TestBuildConfigJson:
    """Test config.json building."""

    def test_build_config_with_defaults(self):
        """Test building config with default feature flags."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_template_config = MagicMock()

            with patch("adt_press.utils.web_assets.render_template") as mock_render:
                with patch("os.makedirs"):
                    from adt_press.utils.web_assets import build_config_json

                    build_config_json(
                        mock_template_config,
                        tmpdir,
                        book_title="Test Book",
                        languages=["en", "es"],
                        default_language="en",
                        strategy_config={"speech_strategy": "openai"},
                    )

                    # Should call render_template
                    mock_render.assert_called_once()

                    # Check template context
                    call_args = mock_render.call_args[0]
                    context = call_args[2]
                    assert context["book_title"] == "Test Book"
                    assert context["languages"] == ["en", "es"]
                    assert context["default_language"] == "en"
                    assert "features" in context
                    assert context["features"]["readAloud"] is True

    def test_build_config_with_feature_overrides(self):
        """Test building config with feature overrides."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_template_config = MagicMock()

            with patch("adt_press.utils.web_assets.render_template") as mock_render:
                with patch("os.makedirs"):
                    from adt_press.utils.web_assets import build_config_json

                    build_config_json(
                        mock_template_config,
                        tmpdir,
                        book_title="Test",
                        languages=["en"],
                        default_language="en",
                        strategy_config={},
                        feature_overrides={"notepad": True, "highlight": True},
                    )

                    # Check overrides were applied
                    context = mock_render.call_args[0][2]
                    assert context["features"]["notepad"] is True
                    assert context["features"]["highlight"] is True


class TestBuildWebAssets:
    """Test main build_web_assets orchestrator."""

    def test_build_web_assets_calls_all_functions(self):
        """Test that build_web_assets calls all sub-functions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("adt_press.utils.web_assets.copy_web_assets") as mock_copy:
                with patch("adt_press.utils.web_assets.copy_build_files") as mock_build_files:
                    with patch("adt_press.utils.web_assets.copy_interface_translations") as mock_translations:
                        with patch("adt_press.utils.web_assets.install_dictionaries") as mock_dict:
                            with patch("adt_press.utils.web_assets.install_fontawesome") as mock_fa:
                                with patch("adt_press.utils.web_assets.install_mathjax") as mock_mj:
                                    with patch("adt_press.utils.web_assets.run_npm_build") as mock_npm:
                                        with patch("adt_press.utils.web_assets.bundle_javascript") as mock_bundle:
                                            from adt_press.utils.web_assets import build_web_assets

                                            result = build_web_assets(tmpdir, ["en", "es"], has_math=True)

                                            # All functions should be called
                                            mock_copy.assert_called_once()
                                            mock_build_files.assert_called_once()
                                            mock_translations.assert_called_once_with(tmpdir, ["en", "es"])
                                            mock_dict.assert_called_once_with(tmpdir, ["en", "es"])
                                            mock_fa.assert_called_once()
                                            mock_mj.assert_called_once()
                                            mock_npm.assert_called_once()
                                            mock_bundle.assert_called_once()

                                            assert result == "web assets built"

    def test_build_web_assets_without_languages(self):
        """Test build_web_assets when no languages provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("adt_press.utils.web_assets.copy_web_assets"):
                with patch("adt_press.utils.web_assets.copy_build_files"):
                    with patch("adt_press.utils.web_assets.copy_interface_translations") as mock_translations:
                        with patch("adt_press.utils.web_assets.install_dictionaries") as mock_dict:
                            with patch("adt_press.utils.web_assets.install_fontawesome"):
                                with patch("adt_press.utils.web_assets.install_mathjax"):
                                    with patch("adt_press.utils.web_assets.run_npm_build"):
                                        with patch("adt_press.utils.web_assets.bundle_javascript"):
                                            from adt_press.utils.web_assets import build_web_assets

                                            build_web_assets(tmpdir, [])

                                            # Should not call language-specific functions
                                            mock_translations.assert_not_called()
                                            mock_dict.assert_not_called()
