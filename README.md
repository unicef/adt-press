[![Ruff](https://github.com/unicef/adt-press/actions/workflows/ruff.yml/badge.svg)](https://github.com/unicef/adt-press/actions/workflows/ruff.yml)
[![Unit Tests](https://github.com/unicef/adt-press/actions/workflows/test.yml/badge.svg)](https://github.com/unicef/adt-press/actions/workflows/test.yml)
[![Deploy Sample](https://github.com/unicef/adt-press/actions/workflows/deploy.yml/badge.svg)](https://github.com/unicef/adt-press/actions/workflows/deploy.yml)
[![Coverage badge](https://github.com/unicef/adt-press/raw/python-coverage-comment-action-data/badge.svg)](https://github.com/unicef/adt-press/tree/python-coverage-comment-action-data)

# ADT Press

A tool for converting PDF files into Accessible Digital Textbooks, ADTs.

The [sample report](https://adtpress.z1.web.core.windows.net/sample/) can help in better understanding the process and outputs or you can view the final [ADT (Accessible Digital Textbook)](https://adtpress.z1.web.core.windows.net/sample/adt/sec_p1_s0.html).

Demos of ADTs created from the outputs of ADT Press:
 * [Momo Multilingual](https://unicef.github.io/adt-momo-storybook/) - Momo and the Leopards, multi-lingual reader from Bhutan (no edits, pure AI output).
 * [Queremos](https://unicef.github.io/adt-queremos-participar/) - Informative reader from Uruguay (lightly edited). 
 * [Cuaderno5 Chapter 1](https://unicef.github.io/ADT-cuaderno5-chapter1/) - Uruguay Grade 5 textbook with Activities (more extensively edited). 

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
- **You must set the environment variable `OPENAI_API_KEY` with your OpenAI API key for the application to work.**

## Installation

This project uses `uv` for dependency management. If you don't have `uv` installed, you can install it following the instructions at [the uv documentation](https://github.com/astral-sh/uv).

### Setting up with UV

Clone the repository and install dependencies:

```bash
git clone git@github.com:unicef/adt-press.git
cd adt-press
uv sync
```

## Usage

### Basic Usage

Run the main script with the default configuration:

```bash
uv run adt-press.py label=raven pdf_path=assets/raven.pdf
```

### Configuration

The application uses OmegaConf for configuration management. The default configuration file is located at `config/config.yaml`.

To override configuration values from the command line:

```bash
uv run adt-press.py label=mydocument pdf_path=/path/to/your/document.pdf page_range.start=0 page_range.end=5
```

### Key Configuration Parameters

- `label`: The label for this PDF file, will be used as the subdirectory name under `output_dir`
- `pdf_path`: Path to the PDF file to process
- `page_range`: Range of pages to process (start and end)
- `output_dir`: Base directory to store outputs
- `template_dir`: Directory containing HTML templates
- `clear_cache`: Whether to clear the processing cache before the run
- `render_strategy`: Controls which strategy to use for layout generation
  - `dynamic` (by default) - detects `layout_types` and routes them to render strategies
  - `two_column` works best for novels and storybooks
  - `html` works best for textbooks
  - `overlay` works best for comic books

## Output

The application generates the following outputs in the `output/[your label]` directory:

- Extracted images from the PDF
- Cropped images
- HTML reports with analysis results
- Visualization of the processing pipeline

## Evaluation Framework

adt-press includes an evaluation tool used for measuring performance of the various LLM tasks against a gold standard. To run the tool make sure you have the following environment variables set:

```bash
LABEL_STUDIO_HOST=[Your LabelStudio Hostname]
LABEL_STUDIO_TOKEN=[Your LabelStudio API Token]
AZURE_STORAGE_ACCOUNT_NAME=[Azure storage account name]
AZURE_STORAGE_ACCOUNT_KEY=[Azure storage account key]
MLFLOW_TRACKING_URI=https://[MLFlow endpoint URL] (optional)
```

Once the environment is set, you can run the adt-eval.py tool the same as the adt-press.py tool, by default, output is put in `output/eval`
```bash
uv run adt-eval.py
```

This will create new reports with results against the gold standard in the output directory. Start at `index.html`.

Alternatively, you can configure various options from the command line, look in `config/eval_config.yml` for a full list. (as well as `config/config.yml` for global options)

```bash
// limit to only run the first 10 test cases and only the text_type task
uv run adt-eval.py label=evals eval.limit=10 eval.tasks=text_type
```

## Development

### Code Style

This project uses Ruff for code formatting and linting. The configuration is specified in `ruff.toml`.

To check code style:

```bash
uv run ruff check --fix
```

To format code:

```bash
uv run ruff format
```

### Testing

Run tests with pytest:

```bash
uv run pytest
```

### Project Structure

- `adt_press/`: Main package
  - `llm/`: LLM integration modules
  - `nodes/`: Hamilton nodes for the processing pipeline
  - `utils/`: Utility functions
  - `models/`: Data models used in adt-press
- `assets/`: Example files
- `config/`: Configuration files
- `prompts/`: LLM prompt templates
- `templates/`: HTML templates
- `tests/`: Test files

## Docker

Build the image:

```bash
docker build -t adt-press .
```

Run the container:

```bash
docker run --rm adt-press
```

To run a specific command inside the container (for example, to execute `uv run adt-press.py` with a PDF file):

```bash
docker run --rm adt-press uv run adt-press.py label=raven pdf_path=assets/raven.pdf
```

Replace `/data/yourfile.pdf` with the path to your PDF file inside the container.

---

#### VS Code: "Reopen in Container"

If you use Visual Studio Code, you can take advantage of the **"Reopen in Container"** feature for a full-featured development environment inside Docker.  
This allows you to edit, run, and debug your code directly within the container.

To use this, add a `.devcontainer` configuration to your project and select "Reopen in Container" from the VS Code command palette.  
You will need to have the **Dev Containers** extension installed in VS Code to use this feature.

---

**Note:**  
The folder `.devcontainer` needs to be in the root of your project, containing a `devcontainer.json` file with the following content:

```json
{
  "name": "ADT Press",
  "build": {
    // Sets the run context to one level up instead of the .devcontainer folder.
    "context": "..",
    // Update the 'dockerFile' property if you aren't using the standard 'Dockerfile' filename.
    "dockerfile": "../Dockerfile"
  }
}
```

---

**Environment Variable Required**

> **Note:**  
> You must set the environment variable `OPENAI_API_KEY` with your OpenAI API key for the application to work.
>
> - When running the Dockerized version, you need to set the `OPENAI_API_KEY` variable every time you run the container.  
>   For example:
>   ```bash
>   docker run --rm -e OPENAI_API_KEY=your-key-here adt-press
>   ```
> - When using VS Code "Reopen in Container", you can add the variable to your `.env` file or set it in the container terminal before running your scripts.

**License**

This project is licensed under the [Apache License 2.0](LICENSE).

