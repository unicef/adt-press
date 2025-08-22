# ADT Press
ADT Press is a Python 3.13+ application that converts PDF files into Accessible Digital Textbooks (ADTs) using AI/LLM processing. The tool extracts text and images from PDFs, processes them through OpenAI's models for analysis, and generates interactive HTML-based accessible textbooks with features like text-to-speech, translations, and educational activities.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap, Build, and Test
- Install UV package manager: `pip install uv`
- Install system dependencies: `sudo apt update && sudo apt install -y libcairo2-dev pkg-config python3-dev`
- Sync dependencies: `uv sync --dev` - takes 5-10 seconds. NEVER CANCEL.
- Run linting: `uv run ruff check` - takes under 1 second.
- Run formatting: `uv run ruff format --check` - takes under 1 second.
- Run tests: `uv run pytest -v` - takes 30-40 seconds. NEVER CANCEL. Set timeout to 60+ seconds.
  - 2 tests will fail without OPENAI_API_KEY environment variable - this is expected
  - All other tests (28+) should pass

### Prerequisites
- **CRITICAL**: Must set `OPENAI_API_KEY` environment variable with valid OpenAI API key
- Python 3.13+ (UV automatically downloads and manages this)
- System dependencies: libcairo2-dev, pkg-config, python3-dev

### Running the Application
- Basic usage: `uv run python adt-press.py label=mydocument pdf_path=/path/to/document.pdf`
- Example with sample file: `uv run python adt-press.py label=test pdf_path=assets/momo.pdf`
- Configuration override: `uv run python adt-press.py label=test pdf_path=assets/momo.pdf page_range.start=0 page_range.end=5`
- **Processing time**: Can take 10-30+ minutes depending on PDF size and page count. NEVER CANCEL.

## Validation

### Manual Testing Requirements
- Always run the bootstrap steps before testing changes
- Test with sample PDFs: `assets/momo.pdf` or `assets/cuaderno3.pdf` 
- **ALWAYS** run linting and tests before committing: `uv run ruff check && uv run ruff format --check && uv run pytest`
- Test configuration changes by running with different parameters
- Verify output generation in `output/[label]/` directory after successful processing

### Build Time Expectations
- UV sync: 5-10 seconds
- Linting: Under 1 second  
- Tests: 30-40 seconds (NEVER CANCEL - set 60+ second timeout)
- Full PDF processing: 10-30+ minutes depending on size (NEVER CANCEL - set 45+ minute timeout)

## Key Project Components

### Python Backend (`adt_press/`)
- `pipeline.py`: Main processing pipeline using Hamilton framework
- `nodes/`: Hamilton nodes for PDF processing, image analysis, text extraction
- `llm/`: LLM integration modules for OpenAI models
- `models/`: Pydantic data models for validation
- `utils/`: Utility functions for file handling, synchronization

### Configuration (`config/`)
- `config.yaml`: Main configuration file with model settings, prompt templates, filters
- Supports command-line overrides: `parameter.subparam=value`

### Web Frontend (`assets/web/assets/`)
- `base.js`: Main application entry point
- `modules/`: Modular JavaScript components (state, audio, navigation, etc.)
- `activities/`: Educational activity types (multiple choice, sorting, etc.)
- Supports accessibility features: text-to-speech, easy read mode, keyboard navigation

### Templates and Prompts
- `templates/`: HTML templates for output generation
- `prompts/`: Jinja2 templates for LLM prompts
- `assets/prompts/`: Example data for few-shot prompting

## Common Commands Reference

### Development Workflow
```bash
# Fresh setup
pip install uv
sudo apt install -y libcairo2-dev pkg-config python3-dev
uv sync --dev

# Daily development
uv run ruff check --fix          # Fix linting issues
uv run ruff format              # Format code
uv run pytest -v               # Run tests

# Test processing
export OPENAI_API_KEY=your-key-here
uv run python adt-press.py label=test pdf_path=assets/momo.pdf
```

### Repository Structure
```
├── adt-press.py          # Main entry point
├── adt_press/            # Python package
│   ├── llm/             # LLM integrations
│   ├── nodes/           # Hamilton processing nodes
│   ├── models/          # Data models
│   └── utils/           # Utilities
├── assets/              # Sample files and web frontend
├── config/              # Configuration files
├── prompts/             # LLM prompt templates
├── templates/           # HTML templates
├── tests/               # Test suite
├── pyproject.toml       # Python project config
└── ruff.toml           # Linting config
```

## Troubleshooting

### Common Issues
- **OpenAI API errors**: Ensure `OPENAI_API_KEY` is set and valid
- **Pycairo build errors**: Install `libcairo2-dev pkg-config python3-dev`
- **File not found**: Use absolute paths or verify file exists
- **Config errors**: Check parameter names match `config/config.yaml` structure
- **Test failures**: 2 tests require OpenAI API key - others should pass

### Docker Usage  
- **Note**: Docker build may fail in environments with SSL certificate issues
- When working: `docker build -t adt-press .` then `docker run --rm -e OPENAI_API_KEY=your-key adt-press uv run adt-press.py label=test pdf_path=/path/to/file.pdf`

### Development Guidelines
- Use Ruff for code formatting and linting (configured in `ruff.toml`)
- Follow existing patterns in `adt_press/nodes/` for new processing steps
- Add tests in `tests/` following pytest conventions
- Update configuration in `config/config.yaml` for new features
- Web frontend follows modular JavaScript pattern in `assets/web/assets/`

## Performance Notes
- Processing is I/O and API-bound - expect 10-30+ minute processing times
- UV dependency sync is fast (5-10 seconds) 
- Tests run quickly (30-40 seconds) except for integration tests requiring OpenAI
- Image processing and LLM calls are the main bottlenecks in PDF processing