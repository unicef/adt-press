# Azure TTS Regeneration for Amharic Content

This tool regenerates text-to-speech audio files for Amharic content using Azure's custom neural voices, which provide higher quality and more authentic pronunciation for Amharic compared to OpenAI's TTS.

## Prerequisites

1. **Azure Speech Service**:
   - Create an Azure Speech service resource
   - Get your subscription key and region
   - Set environment variables:
     ```bash
     export AZURE_SPEECH_KEY='your-azure-speech-key'
     export AZURE_SPEECH_REGION='eastus'  # or your region
     ```

2. **Python Dependencies**:
   ```bash
   pip install azure-cognitiveservices-speech pydub
   ```
   
   Or if using uv:
   ```bash
   uv pip install azure-cognitiveservices-speech pydub
   ```

## Usage

### Basic Usage

Regenerate audio files for an Amharic output directory:

```bash
python tools/regenerate_amharic_tts_azure.py \
  --input-dir output/ethiopia-test/adt/content/i18n/am
```

This will:
- Read `texts.json` from the input directory
- Generate audio files in `{input-dir}/audio/`
- Use Azure's `am-ET-MekdesNeural` voice (Amharic Ethiopian female voice)

### Custom Output Directory

Save audio files to a different location:

```bash
python tools/regenerate_amharic_tts_azure.py \
  --input-dir output/ethiopia-test/adt/content/i18n/am \
  --output-dir output/ethiopia-test/adt/content/i18n/am/audio_azure
```

### Custom Voice

Use a different Azure neural voice:

```bash
python tools/regenerate_amharic_tts_azure.py \
  --input-dir output/ethiopia-test/adt/content/i18n/am \
  --voice am-ET-AmehaNeural  # Male voice
```

## Available Amharic Voices

Azure provides the following neural voices for Amharic (Ethiopia):

- `am-ET-MekdesNeural` - Female (default)
- `am-ET-AmehaNeural` - Male

## Features

- **Authentic Amharic Pronunciation**: Uses SSML to configure proper Amharic phonology
- **Quality Optimization**: Compresses audio to 64kbps mono MP3 at 24kHz
- **Progress Tracking**: Shows detailed progress as files are generated
- **Error Handling**: Continues processing even if individual files fail
- **Clean Output**: Removes temporary raw files after compression

## Audio Settings

The script generates audio with these settings:
- **Format**: MP3
- **Sample Rate**: 24kHz
- **Bit Rate**: 64kbps
- **Channels**: Mono
- **Voice Rate**: 0.95x (slightly slower for clarity)

## Pronunciation Instructions

The script applies the following pronunciation guidelines via SSML:

- Ejective consonants characteristic of Amharic (p', t', ch', ts', k')
- Geminated (doubled) consonants with longer duration
- Seven-vowel system: /ə/, /u/, /i/, /a/, /e/, /ɨ/, /o/
- Proper stress patterns (penultimate syllable)
- Characteristic Amharic intonation and rhythm
- Cheerful and positive tone

## Output Structure

```
output/ethiopia-test/adt/content/i18n/am/
├── texts.json                    # Input: text content
├── audios.json                   # Existing: audio file mapping
└── audio/                        # Output directory
    ├── txt_p1_g0_t0.mp3
    ├── txt_p1_g0_t0_easy_read.mp3
    └── ...
```

## Troubleshooting

### Missing Environment Variables

```
Error: AZURE_SPEECH_KEY and AZURE_SPEECH_REGION environment variables must be set.
```

**Solution**: Set the required environment variables:
```bash
export AZURE_SPEECH_KEY='your-key'
export AZURE_SPEECH_REGION='eastus'
```

### Import Errors

```
Error: Missing required package. No module named 'azure'
```

**Solution**: Install required packages:
```bash
pip install azure-cognitiveservices-speech pydub
```

### Rate Limiting

If you hit Azure rate limits, the script will show errors. Consider:
- Using a higher tier Azure subscription
- Adding delays between requests (modify the script)
- Processing in smaller batches

## Cost Considerations

Azure Speech TTS pricing (as of 2024):
- **Standard**: ~$4 per 1M characters
- **Neural**: ~$16 per 1M characters

The Amharic neural voices use neural pricing. Estimate costs based on your text length.

## Comparison with OpenAI TTS

| Feature | Azure Neural TTS | OpenAI TTS |
|---------|------------------|------------|
| Amharic Support | Native (am-ET) | Limited |
| Pronunciation | Authentic Ethiopian | Generic |
| Voice Options | 2 (Male/Female) | 6 (not Amharic-specific) |
| SSML Support | Full | Instructions only |
| Cost | ~$16/1M chars | ~$15/1M chars |
| Quality | Excellent for Amharic | Good but less natural |

## Integration with ADT Press

After regenerating audio files:

1. The `audios.json` file already exists and maps text IDs to audio filenames
2. Simply replace the audio files in the `audio/` directory
3. The ADT web application will automatically use the new audio files
4. No changes to HTML or JSON files are needed

## Example Workflow

```bash
# Set Azure credentials
export AZURE_SPEECH_KEY='your-key-here'
export AZURE_SPEECH_REGION='eastus'

# Regenerate audio for existing ADT output
python tools/regenerate_amharic_tts_azure.py \
  --input-dir output/ethiopia-test/adt/content/i18n/am

# Check the results
ls -lh output/ethiopia-test/adt/content/i18n/am/audio/

# Open the ADT in browser to test
open output/ethiopia-test/adt/index.html
```

## Future Enhancements

Potential improvements for this script:
- Batch processing with rate limiting
- Resume capability for interrupted runs
- Parallel generation with concurrency limits
- Custom SSML templates per text type
- Voice selection based on gender/age metadata
- Quality comparison reports
