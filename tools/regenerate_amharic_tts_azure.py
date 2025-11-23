#!/usr/bin/env python3
"""
Regenerate TTS audio files for Amharic content using Azure custom neural voices.

This script reads the texts.json file from an Amharic output folder and generates
new audio files using Azure's TTS service with custom neural voices optimized for Amharic.

Requirements:
    - Azure Speech SDK: pip install azure-cognitiveservices-speech
    - pydub: pip install pydub
    - AZURE_SPEECH_KEY and AZURE_SPEECH_REGION environment variables must be set

Usage:
    python tools/regenerate_amharic_tts_azure.py --input-dir output/ethiopia-test/adt/content/i18n/am --output-dir output/ethiopia-test/adt/content/i18n/am/audio

    # Or regenerate in place:
    python tools/regenerate_amharic_tts_azure.py --input-dir output/ethiopia-test/adt/content/i18n/am
"""

import argparse
import asyncio
import json
import os
from pathlib import Path

try:
    import azure.cognitiveservices.speech as speechsdk
    from pydub import AudioSegment
except ImportError as e:
    print(f"Error: Missing required package. {e}")
    print("Please install: pip install azure-cognitiveservices-speech pydub")
    exit(1)


# Azure TTS configuration for Amharic
AZURE_VOICE_NAME = "am-ET-MekdesNeural"  # Amharic (Ethiopia) female voice
AZURE_LANGUAGE_CODE = "am-ET"

# Audio quality settings
SAMPLE_RATE = 24000
BIT_RATE = "64k"
OUTPUT_FORMAT = "mp3"

# Amharic pronunciation instructions
AMHARIC_INSTRUCTIONS = """
Speak in an authentic Ethiopian Amharic accent. Use the pronunciation and phonology typical of native Amharic speakers. Key characteristics:
- Use the ejective consonants characteristic of Amharic (p', t', ch', ts', k')
- Pronounce the geminated (doubled) consonants distinctly with longer duration
- Use the seven-vowel system of Amharic: /ə/, /u/, /i/, /a/, /e/, /ɨ/, /o/
- Maintain proper stress patterns, which typically fall on the penultimate syllable
- Use the characteristic intonation and rhythm of Amharic speech

Speak in a cheerful and positive tone.
"""


def get_azure_config() -> tuple[str, str]:
    """Get Azure Speech configuration from environment variables."""
    speech_key = os.environ.get("AZURE_SPEECH_KEY")
    speech_region = os.environ.get("AZURE_SPEECH_REGION")

    if not speech_key or not speech_region:
        raise ValueError(
            "AZURE_SPEECH_KEY and AZURE_SPEECH_REGION environment variables must be set.\n"
            "Example:\n"
            "  export AZURE_SPEECH_KEY='your-key-here'\n"
            "  export AZURE_SPEECH_REGION='eastus'"
        )

    return speech_key, speech_region


def create_ssml_with_instructions(text: str, voice_name: str = AZURE_VOICE_NAME) -> str:
    """
    Create SSML markup with pronunciation instructions for Amharic.

    Args:
        text: The Amharic text to speak
        voice_name: The Azure neural voice to use

    Returns:
        SSML formatted string
    """
    # Escape XML special characters
    text_escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")

    ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{AZURE_LANGUAGE_CODE}">
    <voice name="{voice_name}">
        <prosody rate="0.95" pitch="0%">
            {text_escaped}
        </prosody>
    </voice>
</speak>"""

    return ssml


async def generate_speech_azure(
    text: str, output_path: str, speech_key: str, speech_region: str, voice_name: str = AZURE_VOICE_NAME
) -> bool:
    """
    Generate speech audio using Azure TTS service.

    Args:
        text: The text to synthesize
        output_path: Path where the audio file should be saved
        speech_key: Azure Speech service key
        speech_region: Azure Speech service region
        voice_name: The neural voice to use

    Returns:
        True if successful, False otherwise
    """
    try:
        # Configure Azure Speech SDK
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio24Khz48KBitRateMonoMp3)

        # Create audio config to save to file
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)

        # Create synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

        # Generate SSML
        ssml = create_ssml_with_instructions(text, voice_name)

        # Synthesize speech
        result = synthesizer.speak_ssml_async(ssml).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(f"  ✓ Generated: {os.path.basename(output_path)}")
            return True
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            print(f"  ✗ Speech synthesis canceled: {cancellation.reason}")
            if cancellation.reason == speechsdk.CancellationReason.Error:
                print(f"    Error details: {cancellation.error_details}")
            return False
        else:
            print(f"  ✗ Unexpected result: {result.reason}")
            return False

    except Exception as e:
        print(f"  ✗ Error generating speech: {e}")
        return False


def compress_audio(input_path: str, output_path: str) -> bool:
    """
    Compress audio file to specified quality settings.

    Args:
        input_path: Path to the input audio file
        output_path: Path where compressed audio should be saved

    Returns:
        True if successful, False otherwise
    """
    try:
        audio = AudioSegment.from_mp3(input_path)
        audio = audio.set_frame_rate(SAMPLE_RATE)
        audio.export(
            output_path,
            format=OUTPUT_FORMAT,
            bitrate=BIT_RATE,
            parameters=["-ac", "1"],  # Mono audio
        )
        return True
    except Exception as e:
        print(f"  ✗ Error compressing audio: {e}")
        return False


async def regenerate_tts_files(texts_json_path: str, output_audio_dir: str, speech_key: str, speech_region: str) -> tuple[int, int]:
    """
    Regenerate all TTS files from a texts.json file.

    Args:
        texts_json_path: Path to the texts.json file
        output_audio_dir: Directory where audio files should be saved
        speech_key: Azure Speech service key
        speech_region: Azure Speech service region

    Returns:
        Tuple of (success_count, failure_count)
    """
    # Load texts
    with open(texts_json_path, "r", encoding="utf-8") as f:
        texts = json.load(f)

    # Create output directory
    os.makedirs(output_audio_dir, exist_ok=True)

    # Create temp directory for raw files
    temp_dir = os.path.join(output_audio_dir, "temp_raw")
    os.makedirs(temp_dir, exist_ok=True)

    success_count = 0
    failure_count = 0

    total = len(texts)
    print(f"\nGenerating {total} audio files...")
    print(f"Voice: {AZURE_VOICE_NAME}")
    print(f"Output: {output_audio_dir}\n")

    for idx, (text_id, text) in enumerate(texts.items(), 1):
        print(f"[{idx}/{total}] {text_id}")

        # Skip empty texts
        if not text or not text.strip():
            print("  ⊘ Skipping empty text")
            continue

        raw_path = os.path.join(temp_dir, f"{text_id}_raw.mp3")
        final_path = os.path.join(output_audio_dir, f"{text_id}.mp3")

        # Generate speech
        success = await generate_speech_azure(text=text, output_path=raw_path, speech_key=speech_key, speech_region=speech_region)

        if success:
            # Compress to final quality
            if compress_audio(raw_path, final_path):
                success_count += 1
                # Clean up raw file
                try:
                    os.remove(raw_path)
                except OSError:
                    pass
            else:
                failure_count += 1
        else:
            failure_count += 1

    # Clean up temp directory
    try:
        os.rmdir(temp_dir)
    except OSError:
        pass

    return success_count, failure_count


def main():
    parser = argparse.ArgumentParser(
        description="Regenerate Amharic TTS files using Azure custom neural voices",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Regenerate with specific output directory
  %(prog)s --input-dir output/ethiopia-test/adt/content/i18n/am \\
           --output-dir output/ethiopia-test/adt/content/i18n/am/audio_new

  # Regenerate in place (overwrites existing audio files)
  %(prog)s --input-dir output/ethiopia-test/adt/content/i18n/am

Environment Variables:
  AZURE_SPEECH_KEY      Azure Speech service subscription key
  AZURE_SPEECH_REGION   Azure Speech service region (e.g., eastus)
        """,
    )

    parser.add_argument(
        "--input-dir", required=True, help="Directory containing texts.json file (e.g., output/ethiopia-test/adt/content/i18n/am)"
    )

    parser.add_argument("--output-dir", help="Directory where audio files should be saved (defaults to {input-dir}/audio)")

    parser.add_argument("--voice", default=AZURE_VOICE_NAME, help=f"Azure neural voice name (default: {AZURE_VOICE_NAME})")

    args = parser.parse_args()

    # Validate input directory
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Error: Input directory does not exist: {input_dir}")
        exit(1)

    texts_json_path = input_dir / "texts.json"
    if not texts_json_path.exists():
        print(f"Error: texts.json not found in {input_dir}")
        exit(1)

    # Determine output directory
    if args.output_dir:
        output_audio_dir = args.output_dir
    else:
        output_audio_dir = str(input_dir / "audio")

    # Get Azure credentials
    try:
        speech_key, speech_region = get_azure_config()
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)

    print("=" * 60)
    print("Amharic TTS Regeneration with Azure Neural Voices")
    print("=" * 60)
    print(f"Input:  {texts_json_path}")
    print(f"Output: {output_audio_dir}")
    print(f"Region: {speech_region}")

    # Run regeneration
    success, failure = asyncio.run(regenerate_tts_files(str(texts_json_path), output_audio_dir, speech_key, speech_region))

    # Print summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"✓ Success: {success}")
    print(f"✗ Failed:  {failure}")
    print(f"  Total:   {success + failure}")

    if failure == 0:
        print("\n✓ All audio files generated successfully!")
    else:
        print(f"\n⚠ {failure} file(s) failed to generate")
        exit(1)


if __name__ == "__main__":
    main()
