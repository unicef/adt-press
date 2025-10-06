import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, List, Tuple

from openai import OpenAI

client = OpenAI()  # Uses OPENAI_API_KEY from environment

SYSTEM_PROMPT = (
    "You are an expert translator. Translate all provided text from Spanish (Uruguay) "
    "to clear, natural English, using language appropriate for a Grade 5 educational textbook. "
    "Keep the translation accurate, age-appropriate, and preserve any technical or educational terminology. "
    "Do not include explanations, just return the translation."
)


def translate_text(text: str) -> str:
    completion = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Translate this: {text}"},
        ],
        max_tokens=1000,
        temperature=0.2,
    )
    return completion.choices[0].message.content.strip()


def extract_strings(data: Any, path=()) -> List[Tuple[Tuple, str]]:
    """
    Recursively extract all (path, string) pairs from nested JSON,
    skipping anything under audioFiles or videoFiles.
    """
    result = []
    # If we're inside an audioFiles or videoFiles block, skip all children
    if any(p in ("audioFiles", "videoFiles") for p in path):
        return result
    if isinstance(data, dict):
        for k, v in data.items():
            result.extend(extract_strings(v, path + (k,)))
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            result.extend(extract_strings(item, path + (idx,)))
    elif isinstance(data, str) and data.strip():
        result.append((path, data))
    return result


def set_value_at_path(data: Any, path: Tuple, value: str):
    """
    Given a nested data structure, set value at the given path.
    """
    obj = data
    for key in path[:-1]:
        obj = obj[key]
    obj[path[-1]] = value


def main(input_path: str, output_path: str, num_workers: int = 6):
    # Load input JSON
    with open(input_path, "r", encoding="utf-8") as f:
        input_json = json.load(f)

    # Step 1: Extract all strings with their paths
    string_paths = extract_strings(input_json)
    total = len(string_paths)

    print(f"Found {total} strings to translate. Starting parallel translation with {num_workers} threads...")

    # Step 2: Translate all strings in parallel
    translated_strings = [None] * total

    def translate_and_print(idx, path, text):
        try:
            translated = translate_text(text)
            print(f"[{idx + 1}/{total}] {path}: {repr(text[:50])} -> {repr(translated[:50])}")
            return (idx, translated)
        except Exception as e:
            print(f"[ERROR] Translating at {path}: {e}")
            return (idx, text)  # Fallback to original if error

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(translate_and_print, idx, path, text) for idx, (path, text) in enumerate(string_paths)]
        for future in as_completed(futures):
            idx, translated = future.result()
            translated_strings[idx] = translated

    # Step 3: Build translated JSON (in-place modification)
    output_json = json.loads(json.dumps(input_json, ensure_ascii=False))  # Deep copy
    for (path, _), translated in zip(string_paths, translated_strings):
        set_value_at_path(output_json, path, translated)

    # Step 4: Save output JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)

    print(f"Translation complete! Output written to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parallel JSON Translator using OpenAI")
    parser.add_argument("--input", "-i", required=True, help="Path to input JSON file")
    parser.add_argument("--output", "-o", required=True, help="Path to output (translated) JSON file")
    parser.add_argument("--threads", "-t", type=int, default=6, help="Number of parallel threads (default: 6)")
    args = parser.parse_args()
    main(args.input, args.output, num_workers=args.threads)
