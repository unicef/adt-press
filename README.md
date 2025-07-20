[![Ruff](https://github.com/incrementventures/adt-press/actions/workflows/ruff.yml/badge.svg)](https://github.com/incrementventures/adt-press/actions/workflows/ruff.yml)
[![Unit Tests](https://github.com/incrementventures/adt-press/actions/workflows/test.yml/badge.svg)](https://github.com/incrementventures/adt-press/actions/workflows/test.yml)
[![Deploy Sample](https://github.com/incrementventures/adt-press/actions/workflows/deploy.yml/badge.svg)](https://github.com/incrementventures/adt-press/actions/workflows/deploy.yml)


# ADT Press

A tool for converting PDF files into Accessible Digital Textbooks, ADTs.

The [sample report](https://incrementventures.github.io/adt-press/) can help in better understanding the process and outputs.

## Features

- PDF document processing and image extraction
- Image analysis using LLM models:
  - Image captioning
  - Intelligent image cropping
  - Image meaningfulness assessment
- HTML report generation
- Visualization of the processing pipeline

## Requirements

- Python 3.13 or higher
- UV package manager (recommended)

## Installation

This project uses `uv` for dependency management. If you don't have `uv` installed, you can install it following the instructions at [the uv documentation](https://github.com/astral-sh/uv).

### Setting up with UV

Clone the repository and install dependencies:

```bash
% git clone git@github.com:incrementventures/adt-press.git
% cd adt-press
% uv sync
```

## Usage

### Basic Usage

Run the main script with the default configuration:

```bash
% uv run adt-press.py pdf_path=/path/to/your/document.pdf
```

### Configuration

The application uses OmegaConf for configuration management. The default configuration file is located at `config/config.yaml`.

To override configuration values from the command line:

```bash
% uv run adt-press.py pdf_path=/path/to/your/document.pdf page_range.start=0 page_range.end=5
```

### Key Configuration Parameters

- `pdf_path`: Path to the PDF file to process
- `page_range`: Range of pages to process (start and end)
- `output_dir`: Directory to store output files
- `template_dir`: Directory containing HTML templates
- `clear_cache`: Whether to clear the processing cache before the run

## Output

The application generates the following outputs in the specified output directory:

- Extracted images from the PDF
- Cropped images
- HTML reports with analysis results
- Visualization of the processing pipeline

## Development

### Code Style

This project uses Ruff for code formatting and linting. The configuration is specified in `ruff.toml`.

To check code style:

```bash
ruff check .
```

To format code:

```bash
ruff format .
```

### Testing

Run tests with pytest:

```bash
python -m pytest tests/
```

### Project Structure

- `adt_press/`: Main package
  - `llm/`: LLM integration modules
  - `nodes/`: Hamilton nodes for the processing pipeline
  - `utils/`: Utility functions
- `assets/`: Example files
- `config/`: Configuration files
- `prompts/`: LLM prompt templates
- `templates/`: HTML templates
- `tests/`: Test files