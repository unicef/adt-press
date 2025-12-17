# ADT Press
ADT Press converts PDF files into Accessible Digital Textbooks (ADTs) using AI/LLM processing. It extracts content from PDFs, processes them through generative AI models (typically from OpenAI), and generates interactive HTML textbooks with text-to-speech, translations, and educational activities.

## Quick Start

**Prerequisites**: Python 3.13+, `OPENAI_API_KEY` environment variable, system dependencies (`libcairo2-dev pkg-config python3-dev`)

```bash
# Setup (macOS/Linux)
pip install uv
uv sync --dev                    # 5-10s - NEVER CANCEL

# Run (10-30+ minutes depending on PDF size - NEVER CANCEL)
uv run python adt-press.py label=test pdf_path=assets/momo.pdf

# Test & Lint
uv run pytest -v                 # 30-40s - expect 2 failures without OPENAI_API_KEY
uv run ruff check --fix
uv run ruff format
```

## Architecture: Hamilton DAG Pipeline

The core is a **Hamilton dataflow pipeline** (`adt_press/pipeline.py`) where functions define nodes in a directed acyclic graph. Hamilton automatically resolves dependencies and executes nodes in order.

**Key Pattern**: Functions in `adt_press/nodes/` define the DAG. Function names become node names, parameters specify dependencies on other nodes or config values:

```python
# nodes/pdf_nodes.py
def pdf_images(pdf_pages: list[Page]) -> list[Image]:
    # Hamilton auto-injects pdf_pages from upstream node
    return [img for page in pdf_pages for img in page.images]
```

**Conditional Execution**: Use `@config.when()` to enable/disable features via config strategies:

```python
@config.when(crop_strategy="llm")
def cropped_images__llm(images, config):  # Runs when crop_strategy=llm
    return crop_with_llm(images, config)

@config.when(crop_strategy="none") 
def cropped_images__none(images):         # Runs when crop_strategy=none
    return images
```

Config strategies control pipeline behavior: `crop_strategy`, `glossary_strategy`, `caption_strategy`, `activity_strategy`, `speech_strategy`, `easy_read_strategy`. Set to `llm` or `none` in `config/config.yaml` or via CLI (`crop_strategy=llm`).

## Configuration System

**Three-layer merge** (OmegaConf): `config/config.yaml` → `output/[label]/config.yaml` → CLI args

```bash
# Override any config value via CLI
uv run python adt-press.py label=test pdf_path=assets/momo.pdf \
  page_range.start=0 page_range.end=5 \
  crop_strategy=llm caption_strategy=none
```

**Critical config sections**:
- `section_types`: Defines content categories (front_cover, text_and_images, activity_matching, etc.) with descriptions LLMs use for classification
- `render_strategies`: Maps section types to HTML generation approaches (template, html, activity)
- `prompts`: LLM prompt configs (model, template_path, rate_limit, max_retries)

When adding features, update `config/config.yaml` schema and reference config nodes in `adt_press/nodes/config_nodes.py`.

## LLM Integration Patterns

All LLM calls follow this structure (`adt_press/llm/*.py`):

1. Define Pydantic response model inheriting `CleanTextBaseModel` (auto-cleans Unicode)
2. Use `get_instructor_client()` for structured outputs
3. Load prompt via `banks.Prompt` from Jinja2 templates in `prompts/`
4. Batch async calls with `gather_with_limit()` for rate limiting

```python
# Example: adt_press/llm/image_caption.py
from adt_press.llm import get_instructor_client
from adt_press.utils.encoding import CleanTextBaseModel

class CaptionResponse(CleanTextBaseModel):
    caption: str
    reasoning: str

async def get_image_caption(config, page, image, language_code):
    prompt = Prompt(cached_read_text_file(config.template_path))
    client = get_instructor_client()
    response = await client.chat.completions.create(
        model=config.model,
        response_model=CaptionResponse,
        messages=[m.model_dump() for m in prompt.chat_messages(context)]
    )
    return ImageCaption(image_id=image.image_id, caption=response.caption)
```

**Rate limiting**: `gather_with_limit(tasks, rate_limit)` enforces `rate_limit` ops/minute across all LLM calls in a batch.

## Adding New Features

**To add a new LLM processing step**:

1. Create `adt_press/llm/my_feature.py` with async function + Pydantic model
2. Add node in `adt_press/nodes/*.py` that calls your LLM function via `gather_with_limit()`
3. Add conditional execution with `@config.when(my_strategy="llm")` and `@config.when(my_strategy="none")`
4. Add `my_strategy: llm` to `config/config.yaml`
5. Add prompt config under `prompts.my_feature` in `config/config.yaml`
6. Create Jinja2 template in `prompts/my_feature.jinja2`
7. Import new node module in `adt_press/pipeline.py` modules list
8. Add tests in `tests/test_my_feature.py`
9. Add a report section template in `templates/` if needed

## Web Frontend

Modular JavaScript in `assets/web/assets/`: `base.js` initializes modules from `modules/` (state, audio, navigation, translations). Activity types in `modules/activities/` follow a plugin pattern with `init()` and `validate()` methods.

## Testing & Quality

- Tests use pytest with fixtures for config/data
- Two tests require `OPENAI_API_KEY` (integration tests) - all others should pass
- Test timeout: 60+ seconds (some tests process PDFs)
- Coverage tracked via GitHub Actions
- Ruff for linting/formatting (configured in `ruff.toml`)

## Troubleshooting

- **"Model not found" errors**: Check `default_model` in config (currently `gpt-5`). Use `print_available_models=true` to list valid models.
- **Pipeline cache issues**: Run with `clear_cache=true` to reset: `uv run python adt-press.py clear_cache=true label=test pdf_path=...`
- **Hamilton node errors**: Check function names don't conflict. Hamilton uses function names as node IDs - duplicate names break the DAG.
- **Config validation errors**: OmegaConf struct mode enforces schema. All CLI params must exist in `config/config.yaml`.
