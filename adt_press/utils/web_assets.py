import os
import shutil
import subprocess
from typing import Any

from adt_press.models.config import TemplateConfig
from adt_press.utils.html import render_template


def copy_interface_translations(run_output_dir_config: str, languages: list[str]) -> None:
    """Copy only the required language interface translations to the output directory."""
    adt_dir = os.path.join(run_output_dir_config, "adt")
    interface_translations_dir = os.path.join(adt_dir, "assets", "interface_translations")

    # Remove existing interface translations
    if os.path.exists(interface_translations_dir):
        shutil.rmtree(interface_translations_dir)

    # Create interface_translations directory and copy only required languages
    os.makedirs(interface_translations_dir, exist_ok=True)
    source_interface_dir = os.path.join("assets", "web", "assets", "interface_translations")

    for language in languages:
        source_lang_dir = os.path.join(source_interface_dir, language)
        target_lang_dir = os.path.join(interface_translations_dir, language)

        if os.path.exists(source_lang_dir):
            shutil.copytree(source_lang_dir, target_lang_dir, dirs_exist_ok=True)


def install_dictionaries(run_output_dir_config: str, languages: list[str]) -> None:
    """Install only the required language dictionaries to the output directory using npm."""
    adt_dir = os.path.join(run_output_dir_config, "adt")
    build_dir = os.path.join(run_output_dir_config, "build")
    dictionaries_dir = os.path.join(adt_dir, "assets", "libs", "dictionaries")

    # Remove existing dictionaries
    if os.path.exists(dictionaries_dir):
        shutil.rmtree(dictionaries_dir)

    # Create dictionaries directory
    os.makedirs(dictionaries_dir, exist_ok=True)

    # Install dictionaries via npm for each language
    for language in languages:
        try:
            # Install the dictionary package (e.g., dictionary-en, dictionary-es, etc.)
            package_name = f"dictionary-{language}"
            subprocess.run(
                ["npm", "install", package_name],
                cwd=build_dir,
                check=True,
                capture_output=True,
                text=True,
            )

            # Copy the dictionary files from node_modules to our dictionaries directory
            source_dict_dir = os.path.join(build_dir, "node_modules", package_name)
            target_lang_dir = os.path.join(dictionaries_dir, language)

            if os.path.exists(source_dict_dir):
                os.makedirs(target_lang_dir, exist_ok=True)

                # Copy the main dictionary files (.aff, .dic, index.js)
                for filename in ["index.aff", "index.dic", "index.js"]:
                    source_file = os.path.join(source_dict_dir, filename)
                    if os.path.exists(source_file):
                        shutil.copy2(source_file, os.path.join(target_lang_dir, filename))

        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not install dictionary for language '{language}': {e}")
            # Fallback to copying from local assets if npm install fails
            source_lang_dir = os.path.join("assets", "web", "assets", "libs", "dictionaries", language)
            target_lang_dir = os.path.join(dictionaries_dir, language)

            if os.path.exists(source_lang_dir):
                shutil.copytree(source_lang_dir, target_lang_dir, dirs_exist_ok=True)


def copy_web_assets(run_output_dir_config: str) -> None:
    """Copy web assets to the output directory, excluding interface_translations and not overwriting config.json."""
    adt_dir = os.path.join(run_output_dir_config, "adt")
    assets_dir = os.path.join("assets", "web", "assets")
    target_assets_dir = os.path.join(adt_dir, "assets")

    # Create target directory
    os.makedirs(target_assets_dir, exist_ok=True)

    # Copy all items except interface_translations and config.json
    for item in os.listdir(assets_dir):
        if item == "interface_translations":
            continue
        source_path = os.path.join(assets_dir, item)
        target_path = os.path.join(target_assets_dir, item)

        # If item is config.json and already exists, skip
        if item == "config.json" and os.path.exists(target_path):
            continue

        if os.path.isdir(source_path):
            shutil.copytree(source_path, target_path, dirs_exist_ok=True)
        else:
            shutil.copy2(source_path, target_path)


def copy_build_files(run_output_dir_config: str) -> None:
    """Copy build configuration files to the output directory."""
    build_dir = os.path.join(run_output_dir_config, "build")
    shutil.rmtree(build_dir, ignore_errors=True)
    os.makedirs(build_dir, exist_ok=True)

    # Copy Makefile
    makefile_path = os.path.join("assets", "web", "utils", "Makefile")
    shutil.copy(makefile_path, os.path.join(build_dir, "Makefile"))

    # Copy package.json
    package_path = os.path.join("assets", "web", "utils", "package.json")
    shutil.copy(package_path, os.path.join(build_dir, "package.json"))

    # Copy tailwind.config.js
    tailwind_path = os.path.join("assets", "web", "utils", "tailwind.config.js")
    shutil.copy(tailwind_path, os.path.join(build_dir, "tailwind.config.js"))


def install_fontawesome(run_output_dir_config: str) -> None:
    """Install Font Awesome via npm and copy to standard structure."""
    adt_dir = os.path.join(run_output_dir_config, "adt")
    build_dir = os.path.join(run_output_dir_config, "build")
    fontawesome_dir = os.path.join(adt_dir, "assets", "libs", "fontawesome")

    # Remove existing fontawesome
    if os.path.exists(fontawesome_dir):
        shutil.rmtree(fontawesome_dir)

    # Create fontawesome directory
    os.makedirs(fontawesome_dir, exist_ok=True)

    try:
        # Install Font Awesome via npm
        subprocess.run(
            ["npm", "install", "@fortawesome/fontawesome-free"],
            cwd=build_dir,
            check=True,
            capture_output=True,
            text=True,
        )

        # Get Font Awesome source directory
        fa_source = os.path.join(build_dir, "node_modules", "@fortawesome", "fontawesome-free")

        # Copy only the minified CSS file we need
        css_source_file = os.path.join(fa_source, "css", "all.min.css")
        css_target_dir = os.path.join(fontawesome_dir, "css")
        os.makedirs(css_target_dir, exist_ok=True)
        if os.path.exists(css_source_file):
            shutil.copy2(css_source_file, os.path.join(css_target_dir, "all.min.css"))

        # Copy webfonts directory (maintains standard structure)
        webfonts_source_dir = os.path.join(fa_source, "webfonts")
        webfonts_target_dir = os.path.join(fontawesome_dir, "webfonts")
        if os.path.exists(webfonts_source_dir):
            shutil.copytree(webfonts_source_dir, webfonts_target_dir)

    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not install Font Awesome: {e}")
        # Fallback to copying from local assets if npm install fails
        source_fa_dir = os.path.join("assets", "web", "assets", "libs", "fontawesome")
        if os.path.exists(source_fa_dir):
            shutil.copytree(source_fa_dir, fontawesome_dir, dirs_exist_ok=True)


def install_mathjax(run_output_dir_config: str) -> None:
    """Install MathJax via npm and copy to assets/libs directory."""
    adt_dir = os.path.join(run_output_dir_config, "adt")
    build_dir = os.path.join(run_output_dir_config, "build")
    mathjax_dir = os.path.join(adt_dir, "assets", "libs", "mathjax")

    # Remove existing mathjax
    if os.path.exists(mathjax_dir):
        shutil.rmtree(mathjax_dir)

    # Create mathjax directory
    os.makedirs(mathjax_dir, exist_ok=True)

    try:
        # Install MathJax via npm
        subprocess.run(
            ["npm", "install", "mathjax@3"],
            cwd=build_dir,
            check=True,
            capture_output=True,
            text=True,
        )

        # Get MathJax source directory
        mathjax_source = os.path.join(build_dir, "node_modules", "mathjax")

        # Copy the es5 directory which contains the browser-ready files
        es5_source_dir = os.path.join(mathjax_source, "es5")
        es5_target_dir = os.path.join(mathjax_dir, "es5")
        if os.path.exists(es5_source_dir):
            shutil.copytree(es5_source_dir, es5_target_dir)

    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not install MathJax: {e}")
        # Fallback to copying from local assets if npm install fails
        source_mathjax_dir = os.path.join("assets", "web", "assets", "libs", "mathjax")
        if os.path.exists(source_mathjax_dir):
            shutil.copytree(source_mathjax_dir, mathjax_dir, dirs_exist_ok=True)


def run_npm_build(run_output_dir_config: str) -> None:
    """Run npm install and tailwindcss build commands in the ADT output directory."""
    build_dir = os.path.join(run_output_dir_config, "build")

    # Run npm install
    subprocess.run(
        ["npm", "install"],
        cwd=build_dir,
        check=True,
        capture_output=True,
        text=True,
    )

    # Run tailwindcss build
    subprocess.run(
        ["npx", "tailwindcss", "-i", "../adt/assets/tailwind_css.css", "-o", "../adt/content/tailwind_output.css"],
        cwd=build_dir,
        check=True,
        capture_output=True,
        text=True,
    )


def bundle_javascript(run_output_dir_config: str) -> None:
    """Bundle and minify JavaScript files using esbuild."""
    adt_dir = os.path.join(run_output_dir_config, "adt")
    assets_dir = os.path.join(adt_dir, "assets")
    build_dir = os.path.join(run_output_dir_config, "build")

    try:
        # Install esbuild if not already installed
        subprocess.run(
            ["npm", "install", "esbuild"],
            cwd=build_dir,
            check=True,
            capture_output=True,
            text=True,
        )

        # Bundle base.js with all dependencies (activity.js is already imported in base.js)
        # Use absolute paths so esbuild can find files regardless of working directory
        base_input = os.path.abspath(os.path.join(assets_dir, "base.js"))
        base_output = os.path.abspath(os.path.join(assets_dir, "base.bundle.min.js"))

        subprocess.run(
            [
                "npx",
                "esbuild",
                base_input,
                "--bundle",
                "--minify",
                "--sourcemap",
                "--format=esm",
                "--target=es2020",
                f"--outfile={base_output}",
            ],
            cwd=build_dir,
            check=True,
            capture_output=True,
            text=True,
        )

    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not bundle JavaScript: {e}")
        print(f"Error output: {e.stderr}")
        if e.stdout:
            print(f"Standard output: {e.stdout}")
        print("Falling back to unbundled JavaScript files")


def build_config_json(
    template_config: TemplateConfig,
    run_output_dir_config: str,
    *,
    book_title: str,
    languages: list[str],
    default_language: str,
    strategy_config: dict[str, Any],
    output_subdir: str = "adt",
    feature_overrides: dict[str, Any] | None = None,
) -> str:
    """Render config.json for the requested output and apply feature overrides if provided."""

    relative_path = os.path.join(output_subdir, "assets", "config.json")
    absolute_path = os.path.join(run_output_dir_config, relative_path)

    os.makedirs(os.path.dirname(absolute_path), exist_ok=True)

    # Compute feature flags so templates stay deterministic.
    feature_flags: dict[str, Any] = {
        "signLanguage": False,
        "easyRead": strategy_config.get("easy_read_strategy", "none") != "none",
        "glossary": strategy_config.get("glossary_strategy", "none") != "none",
        "eli5": strategy_config.get("explanation_strategy", "none") != "none",
        "readAloud": strategy_config.get("speech_strategy", "none") != "none",
        "autoplay": True,
        "showTutorial": True,
        "showNavigationControls": True,
        "describeImages": True,
        "notepad": False,
        "state": True,
        "characterDisplay": True,
        "highlight": False,
    }

    if feature_overrides:
        feature_flags.update(feature_overrides)

    # Prepare template context with feature overrides merged in
    template_context = {
        "languages": languages,
        "default_language": default_language,
        "book_title": book_title,
        "config": strategy_config,
        "features": feature_flags,
    }

    render_template(
        template_config,
        "config.json",
        template_context,
        output_name=relative_path,
    )

    return absolute_path


def build_web_assets(run_output_dir_config: str, languages: list[str]) -> str:
    """Builds web assets by copying all files and running npm commands."""
    # Copy all web assets
    copy_web_assets(run_output_dir_config)

    # Copy build configuration files
    copy_build_files(run_output_dir_config)

    # Copy only required language translations
    if languages:
        copy_interface_translations(run_output_dir_config, languages)
        install_dictionaries(run_output_dir_config, languages)

    # Install Font Awesome
    install_fontawesome(run_output_dir_config)

    # Install MathJax
    install_mathjax(run_output_dir_config)

    # Run npm build process
    run_npm_build(run_output_dir_config)

    # Bundle JavaScript files
    bundle_javascript(run_output_dir_config)

    return "web assets built"
