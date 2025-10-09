import os
import shutil
import subprocess


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
            subprocess.run(["npm", "install", package_name], cwd=adt_dir, check=True, capture_output=True, text=True)

            # Copy the dictionary files from node_modules to our dictionaries directory
            source_dict_dir = os.path.join(adt_dir, "node_modules", package_name)
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
    adt_dir = os.path.join(run_output_dir_config, "adt")

    # Copy Makefile
    makefile_path = os.path.join("assets", "web", "utils", "Makefile")
    shutil.copy(makefile_path, os.path.join(adt_dir, "Makefile"))

    # Copy package.json
    package_path = os.path.join("assets", "web", "utils", "package.json")
    shutil.copy(package_path, os.path.join(adt_dir, "package.json"))

    # Copy tailwind.config.js
    tailwind_path = os.path.join("assets", "web", "utils", "tailwind.config.js")
    shutil.copy(tailwind_path, os.path.join(adt_dir, "tailwind.config.js"))


def run_npm_build(run_output_dir_config: str) -> None:
    """Run npm install and tailwindcss build commands in the ADT output directory."""
    adt_dir = os.path.join(run_output_dir_config, "adt")

    # Run npm install
    subprocess.run(["npm", "install"], cwd=adt_dir, check=True)

    # Run tailwindcss build
    subprocess.run(["npx", "tailwindcss", "-i", "assets/tailwind_css.css", "-o", "content/tailwind_output.css"], cwd=adt_dir, check=True)


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

    # Run npm build process
    run_npm_build(run_output_dir_config)

    return "web assets built"
