import os
import subprocess


def build_web_assets(run_output_dir_config: str) -> str:
    """Runs npm install and npx build in the ADT output directory after assets are copied."""
    adt_dir = os.path.join(run_output_dir_config, "adt")
    # Run npm install
    subprocess.run(["npm", "install"], cwd=adt_dir, check=True)
    # Run npx (replace 'npx tailwindcss build ...' with your actual command)
    subprocess.run(["npx", "tailwindcss", "-i", "assets/tailwind_css.css", "-o", "content/tailwind_output.css"], cwd=adt_dir, check=True)
    return "web assets built"
