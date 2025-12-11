"""Utilities for processing report assets, including Tailwind CSS compilation."""

import json
import os
import shutil
import subprocess

import structlog

logger = structlog.get_logger()


def compile_tailwind_for_reports(
    output_dir: str,
    report_files: list[str],
) -> str:
    """
    Compile Tailwind CSS for generated report HTML files.

    Scans all report HTML files to detect used Tailwind classes and generates
    a minimal CSS file containing only the classes that are actually used.

    Args:
        output_dir: Base output directory containing report files
        report_files: List of absolute paths to report HTML files

    Returns:
        Path to the compiled Tailwind CSS file

    Raises:
        RuntimeError: If Tailwind CLI compilation fails
    """
    # Verify all files exist
    missing_files = [path for path in report_files if not os.path.exists(path)]
    if missing_files:
        logger.warning(
            "Some report files not found, skipping compilation",
            missing_count=len(missing_files),
        )
        return ""

    # Create build directory for npm/tailwind operations
    build_dir = os.path.join(output_dir, "build_reports")
    os.makedirs(build_dir, exist_ok=True)

    # Copy package.json to build directory
    package_source = os.path.join("assets", "web", "utils", "package.json")
    package_dest = os.path.join(build_dir, "package.json")
    shutil.copy2(package_source, package_dest)

    # Convert absolute paths to relative paths from build_dir
    relative_paths = [os.path.relpath(path, build_dir) for path in report_files]
    content_paths = json.dumps(relative_paths)

    # Create temporary Tailwind config in build directory
    config_path = os.path.join(build_dir, "tailwind.config.js")
    with open(config_path, "w", encoding="utf-8") as config_file:
        config_content = f"""
/** @type {{import('tailwindcss').Config}} */
module.exports = {{
  content: {content_paths},
  theme: {{
    extend: {{
      keyframes: {{
        tutorialPopIn: {{
          '0%': {{ opacity: '0', transform: 'scale(0.9)' }},
          '100%': {{ opacity: '1', transform: 'scale(1)' }},
        }},
        pulseBorder: {{
          '0%': {{ boxShadow: '0 0 0 0 rgba(49,130,206,0.7)' }},
          '70%': {{ boxShadow: '0 0 0 10px rgba(49,130,206,0)' }},
          '100%': {{ boxShadow: '0 0 0 0 rgba(49,130,206,0)' }},
        }},
      }},
      animation: {{
        tutorialPopIn: 'tutorialPopIn 0.3s ease-out forwards',
        pulseBorder: 'pulseBorder 2s infinite',
      }},
      boxShadow: {{
        'tutorial': '0 0 0 4px rgba(49,130,206,0.3)',
      }}
    }},
  }},
  plugins: [],
}}
"""
        config_file.write(config_content)

    try:
        # Run npm install to get tailwindcss
        npm_result = subprocess.run(
            ["npm", "install"],
            cwd=build_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )

        if npm_result.returncode != 0:
            logger.error(
                "npm install failed",
                stderr=npm_result.stderr,
            )
            raise RuntimeError(f"npm install failed: {npm_result.stderr}")

        # Output CSS file path
        css_output_path = os.path.join(output_dir, "reports_tailwind.css")

        # Create minimal input CSS for Tailwind
        with open(os.path.join(build_dir, "input.css"), "w", encoding="utf-8") as f:
            f.write("@tailwind base;\n@tailwind components;\n@tailwind utilities;\n")

        # Run Tailwind CLI via npx
        tailwind_result = subprocess.run(
            [
                "npx",
                "tailwindcss",
                "-i",
                "input.css",
                "-c",
                "tailwind.config.js",
                "-o",
                os.path.abspath(css_output_path),
                "--minify",
            ],
            cwd=build_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )

        if tailwind_result.returncode != 0:
            logger.error(
                "Tailwind CSS compilation failed",
                stderr=tailwind_result.stderr,
            )
            raise RuntimeError(f"Tailwind compilation failed: {tailwind_result.stderr}")

        return css_output_path

    finally:
        # Clean up build directory
        try:
            shutil.rmtree(build_dir)
        except OSError as e:
            logger.warning("Failed to clean up build directory", error=str(e))
