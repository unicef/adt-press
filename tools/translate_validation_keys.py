#!/usr/bin/env python3
"""
Script to translate validation feedback keys to all target languages.
"""

import json
import os
from pathlib import Path

from openai import OpenAI

# Base directory for interface translations
BASE_DIR = Path(__file__).parent.parent / "assets/web/assets/interface_translations"

# Languages we've already manually translated
SKIP_LANGUAGES = {"en", "es", "pt"}

# Language code to full language name mapping
LANGUAGE_NAMES = {
    "am": "Amharic",
    "ar": "Arabic",
    "bg": "Bulgarian",
    "bn": "Bengali",
    "bs": "Bosnian",
    "ca": "Catalan",
    "cs": "Czech",
    "cus": "Cushitic",
    "da": "Danish",
    "de": "German",
    "dz": "Dzongkha",
    "el": "Greek",
    "es_uy": "Spanish (Uruguay)",
    "et": "Estonian",
    "fi": "Finnish",
    "fr": "French",
    "gu": "Gujarati",
    "he": "Hebrew",
    "hi": "Hindi",
    "hmn": "Hmong",
    "hr": "Croatian",
    "ht": "Haitian Creole",
    "hu": "Hungarian",
    "hy": "Armenian",
    "id": "Indonesian",
    "is": "Icelandic",
    "it": "Italian",
    "ja": "Japanese",
    "ka": "Georgian",
    "kk": "Kazakh",
    "kn": "Kannada",
    "ko": "Korean",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mi": "Maori",
    "mk": "Macedonian",
    "ml": "Malayalam",
    "mn": "Mongolian",
    "mr": "Marathi",
    "ms": "Malay",
    "my": "Burmese",
    "ne": "Nepali",
    "nl": "Dutch",
    "no": "Norwegian",
    "pa": "Punjabi",
    "pl": "Polish",
    "ro": "Romanian",
    "ru": "Russian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "so": "Somali",
    "sq": "Albanian",
    "sr": "Serbian",
    "sv": "Swedish",
    "sw": "Swahili",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tl": "Tagalog",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "vi": "Vietnamese",
    "zh": "Chinese",
}

# English source text to translate
VALIDATION_KEYS_EN = {
    "validation-inappropriate-language": "Inappropriate language",
    "validation-check-spelling": "Check your spelling",
    "validation-write-appropriate": ("Please write in the appropriate language and use appropriate language"),
    "validation-error": "Validation error",
}


def translate_validation_keys(target_language: str, client: OpenAI) -> dict:
    """Use OpenAI to translate validation keys to target language."""
    prompt = f"""Translate the following validation feedback messages from English to {target_language}.
Keep the translations concise and appropriate for educational content.
Maintain the same tone and formality level.

English texts to translate:
1. "Inappropriate language"
2. "Check your spelling" 
3. "Please write in the appropriate language and use appropriate language"
4. "Validation error"

Provide ONLY the translations as a JSON object with these exact keys:
{{
    "validation-inappropriate-language": "...",
    "validation-check-spelling": "...",
    "validation-write-appropriate": "...",
    "validation-error": "..."
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": ("You are a professional translator. Provide only valid JSON output."),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        content = response.choices[0].message.content
        # Extract JSON from potential markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        translations = json.loads(content)
        return translations

    except Exception as e:
        print(f"    ❌ Translation error: {e}")
        return None


def update_translation_file(file_path: Path, translations: dict, lang_code: str) -> bool:
    """Update a translation file with translated validation keys."""
    try:
        # Read the file
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Update with translations
        for key, value in translations.items():
            data[key] = value

        # Write back with proper formatting
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  ✅ {lang_code}: Translated and updated")
        return True

    except Exception as e:
        print(f"  ❌ {lang_code}: Error updating file - {e}")
        return False


def main():
    """Main function to translate all validation keys."""
    # Check for OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        return

    client = OpenAI(api_key=api_key)

    print("Translating validation keys to all target languages...\n")

    updated_count = 0
    skipped_count = 0
    error_count = 0

    # Get all language directories
    lang_dirs = sorted([d for d in BASE_DIR.iterdir() if d.is_dir()])

    for lang_dir in lang_dirs:
        lang_code = lang_dir.name

        # Skip languages we've already manually translated
        if lang_code in SKIP_LANGUAGES:
            print(f"  ⏭️  {lang_code}: Already manually translated, skipping")
            skipped_count += 1
            continue

        json_file = lang_dir / "interface_translations.json"

        if not json_file.exists():
            print(f"  ⚠️  {lang_code}: File not found")
            continue

        # Get the full language name
        lang_name = LANGUAGE_NAMES.get(lang_code, lang_code)
        print(f"  🔄 {lang_code} ({lang_name}): Translating...")

        # Translate
        translations = translate_validation_keys(lang_name, client)

        if translations:
            # Update file
            success = update_translation_file(json_file, translations, lang_code)
            if success:
                updated_count += 1
            else:
                error_count += 1
        else:
            error_count += 1

    print(f"\n{'=' * 50}")
    print("Summary:")
    print(f"  Translated & updated: {updated_count} files")
    print(f"  Skipped: {skipped_count} files (already done)")
    print(f"  Errors: {error_count} files")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
