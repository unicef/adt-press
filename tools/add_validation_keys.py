#!/usr/bin/env python3
"""
Script to add validation feedback keys to all interface_translations.json files.
"""

import json
from pathlib import Path

# Base directory for interface translations
BASE_DIR = Path(__file__).parent.parent / "assets/web/assets/interface_translations"

# Languages we've already updated
SKIP_LANGUAGES = {"en", "es", "pt"}

# Validation keys to add with English fallback text
VALIDATION_KEYS = {
    "validation-inappropriate-language": "Inappropriate language",
    "validation-check-spelling": "Check your spelling",
    "validation-write-appropriate": "Please write in the appropriate language and use appropriate language",
    "validation-error": "Validation error",
}


def add_validation_keys_to_file(file_path: Path) -> bool:
    """Add validation keys to a single interface_translations.json file."""
    try:
        # Read the file
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check if any validation keys already exist
        has_validation_keys = any(key in data for key in VALIDATION_KEYS.keys())

        if has_validation_keys:
            print(f"  ⏭️  {file_path.parent.name}: Already has validation keys, skipping")
            return False

        # Add the validation keys (using English as fallback)
        for key, value in VALIDATION_KEYS.items():
            data[key] = value

        # Write back with proper formatting
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  ✅ {file_path.parent.name}: Added validation keys")
        return True

    except Exception as e:
        print(f"  ❌ {file_path.parent.name}: Error - {e}")
        return False


def main():
    """Main function to process all language files."""
    print("Adding validation keys to interface_translations.json files...\n")

    updated_count = 0
    skipped_count = 0
    error_count = 0

    # Get all language directories
    lang_dirs = sorted([d for d in BASE_DIR.iterdir() if d.is_dir()])

    for lang_dir in lang_dirs:
        lang_code = lang_dir.name

        # Skip languages we've already manually updated
        if lang_code in SKIP_LANGUAGES:
            print(f"  ⏭️  {lang_code}: Already manually updated, skipping")
            skipped_count += 1
            continue

        json_file = lang_dir / "interface_translations.json"

        if not json_file.exists():
            print(f"  ⚠️  {lang_code}: File not found")
            continue

        result = add_validation_keys_to_file(json_file)

        if result:
            updated_count += 1
        elif result is False and "Already has" not in str(result):
            error_count += 1

    print(f"\n{'=' * 50}")
    print("Summary:")
    print(f"  Updated: {updated_count} files")
    print(f"  Skipped: {skipped_count} files (already done)")
    print(f"  Errors: {error_count} files")
    print(f"{'=' * 50}")

    if updated_count > 0:
        print("\n⚠️  Note: All files use English as fallback text.")
        print("Consider translating these keys for better localization.")


if __name__ == "__main__":
    main()
