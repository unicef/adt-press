"""Tests for report assets compilation."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from adt_press.utils.report_assets import compile_tailwind_for_reports


class TestCompileTailwindForReports:
    """Test Tailwind CSS compilation for reports."""

    def test_missing_files_returns_empty(self):
        """Test that missing files returns empty string."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = compile_tailwind_for_reports(
                output_dir=tmpdir,
                report_files=["/nonexistent/file.html"],
            )
            assert result == ""

    def test_all_files_missing_logs_warning(self):
        """Test that all missing files triggers warning and returns empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = compile_tailwind_for_reports(
                output_dir=tmpdir,
                report_files=[
                    "/nonexistent/file1.html",
                    "/nonexistent/file2.html",
                ],
            )
            assert result == ""

    def test_successful_compilation(self):
        """Test successful Tailwind compilation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy HTML files
            report1 = os.path.join(tmpdir, "report1.html")
            report2 = os.path.join(tmpdir, "report2.html")
            
            Path(report1).write_text("<div class='text-xl font-bold'>Test</div>")
            Path(report2).write_text("<div class='bg-blue-500 p-4'>Test</div>")

            # Mock npm install success
            mock_npm = MagicMock(returncode=0, stdout="", stderr="")
            # Mock tailwind compilation success
            mock_tailwind = MagicMock(returncode=0, stdout="Done", stderr="")

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [mock_npm, mock_tailwind]
                
                # Mock package.json copy
                with patch("shutil.copy2"):
                    result = compile_tailwind_for_reports(
                        output_dir=tmpdir,
                        report_files=[report1, report2],
                    )

            expected_css = os.path.join(tmpdir, "reports_tailwind.css")
            assert result == expected_css
            
            # Verify subprocess was called correctly
            assert mock_run.call_count == 2
            
            # Check npm install call
            npm_call = mock_run.call_args_list[0]
            assert npm_call[0][0] == ["npm", "install"]
            assert npm_call[1]["cwd"] == os.path.join(tmpdir, "build_reports")
            assert npm_call[1]["capture_output"] is True
            
            # Check tailwindcss call
            tailwind_call = mock_run.call_args_list[1]
            assert "tailwindcss" in tailwind_call[0][0]

    def test_npm_install_failure(self):
        """Test handling of npm install failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report = os.path.join(tmpdir, "report.html")
            Path(report).write_text("<div>Test</div>")

            mock_npm = MagicMock(returncode=1, stdout="", stderr="npm error: package not found")

            with patch("subprocess.run", return_value=mock_npm):
                with patch("shutil.copy2"):
                    with pytest.raises(RuntimeError, match="npm install failed"):
                        compile_tailwind_for_reports(
                            output_dir=tmpdir,
                            report_files=[report],
                        )

    def test_tailwind_compilation_failure(self):
        """Test handling of Tailwind compilation failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report = os.path.join(tmpdir, "report.html")
            Path(report).write_text("<div>Test</div>")

            mock_npm = MagicMock(returncode=0, stdout="", stderr="")
            mock_tailwind = MagicMock(
                returncode=9, 
                stdout="", 
                stderr="Input file does not exist"
            )

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [mock_npm, mock_tailwind]
                
                with patch("shutil.copy2"):
                    with pytest.raises(
                        RuntimeError, 
                        match="Tailwind compilation failed"
                    ):
                        compile_tailwind_for_reports(
                            output_dir=tmpdir,
                            report_files=[report],
                        )

    def test_uses_existing_css(self):
        """Test that function returns existing CSS file if tailwind already run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create existing CSS file
            css_path = os.path.join(tmpdir, "reports_tailwind.css")
            Path(css_path).write_text("/* existing css */")
            
            report = os.path.join(tmpdir, "web_report.html")
            Path(report).write_text("<div class='container'>Content</div>")

            mock_npm = MagicMock(returncode=0, stdout="", stderr="")
            mock_tailwind = MagicMock(returncode=0, stdout="", stderr="")

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [mock_npm, mock_tailwind]
                
                with patch("shutil.copy2"):
                    result = compile_tailwind_for_reports(
                        output_dir=tmpdir,
                        report_files=[report],
                    )
                    
                    # Should return the CSS path
                    assert result == css_path

    def test_cleanup_on_success(self):
        """Test that build directory is cleaned up on successful compilation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report = os.path.join(tmpdir, "report.html")
            Path(report).write_text("<div>Test</div>")

            mock_npm = MagicMock(returncode=0, stdout="", stderr="")
            mock_tailwind = MagicMock(returncode=0, stdout="", stderr="")

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [mock_npm, mock_tailwind]
                
                with patch("shutil.copy2"):
                    with patch("shutil.rmtree") as mock_rmtree:
                        compile_tailwind_for_reports(
                            output_dir=tmpdir,
                            report_files=[report],
                        )
                        
                        # Verify cleanup was attempted
                        mock_rmtree.assert_called_once()
                        build_dir = os.path.join(tmpdir, "build_reports")
                        assert mock_rmtree.call_args[0][0] == build_dir

    def test_cleanup_on_failure(self):
        """Test that build directory cleanup is attempted even on failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report = os.path.join(tmpdir, "report.html")
            Path(report).write_text("<div>Test</div>")

            mock_npm = MagicMock(returncode=1, stdout="", stderr="error")

            with patch("subprocess.run", return_value=mock_npm):
                with patch("shutil.copy2"):
                    with patch("shutil.rmtree") as mock_rmtree:
                        with pytest.raises(RuntimeError):
                            compile_tailwind_for_reports(
                                output_dir=tmpdir,
                                report_files=[report],
                            )
                        
                        # Cleanup should still be attempted
                        mock_rmtree.assert_called_once()
