# LLM Provider System

ADT Press now supports multiple LLM providers through a flexible abstraction layer. You can easily switch between OpenAI, Google Gemini, and Anthropic Claude, or add support for new providers.

## Supported Providers

- **OpenAI** (default): GPT-4, GPT-3.5, and other OpenAI models
- **Google Gemini**: Gemini Pro, Gemini 1.5 Pro, and other Gemini models
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus, and other Claude models

## Configuration

### Via config.yaml

Edit your `config/config.yaml` file to specify the LLM provider:

```yaml
# LLM provider configuration
llm_provider:
  provider: openai # or 'gemini', 'anthropic'
  api_key: null # optional - uses environment variable if not specified
  base_url: null # optional - for custom endpoints (e.g., Azure OpenAI)

default_model: gpt-4 # or 'gemini-pro', 'claude-3-5-sonnet-20241022'
```

### Via Environment Variables

You can also configure the provider using environment variables:

```bash
# Set the provider type
export LLM_PROVIDER=gemini  # or 'openai', 'anthropic'

# Set the appropriate API key
export GEMINI_API_KEY=your-api-key-here
# or
export OPENAI_API_KEY=your-api-key-here
# or
export ANTHROPIC_API_KEY=your-api-key-here

# Optional: Custom base URL
export LLM_BASE_URL=https://your-custom-endpoint.com
```

### Via Command Line

Override provider settings at runtime:

```bash
uv run python adt-press.py \
  label=test \
  pdf_path=assets/momo.pdf \
  llm_provider.provider=gemini \
  default_model=gemini-1.5-pro
```

## Model Name Formatting

The system automatically formats model names for each provider:

### OpenAI

Models are used as-is:

- `gpt-4` → `gpt-4`
- `gpt-5.2` → `gpt-5.2`

### Gemini

Models are prefixed with `gemini/`:

- `gemini-pro` → `gemini/gemini-pro`
- `gemini-1.5-pro` → `gemini/gemini-1.5-pro`
- `pro` → `gemini/gemini-pro` (shorthand)

### Anthropic

Models are prefixed with `claude-` if not already:

- `claude-3-5-sonnet-20241022` → `claude-3-5-sonnet-20241022`
- `3-5-sonnet-20241022` → `claude-3-5-sonnet-20241022`

## Usage Examples

### Using OpenAI (default)

```bash
export OPENAI_API_KEY=your-key
uv run python adt-press.py label=test pdf_path=assets/momo.pdf
```

### Using Google Gemini

```bash
export GEMINI_API_KEY=your-key
uv run python adt-press.py \
  label=test \
  pdf_path=assets/momo.pdf \
  llm_provider.provider=gemini \
  default_model=gemini-1.5-pro
```

### Using Anthropic Claude

```bash
export ANTHROPIC_API_KEY=your-key
uv run python adt-press.py \
  label=test \
  pdf_path=assets/momo.pdf \
  llm_provider.provider=anthropic \
  default_model=claude-3-5-sonnet-20241022
```

## Adding New Providers

To add support for a new LLM provider:

1. **Create a provider class** in `adt_press/llm/providers.py`:

```python
class MyNewProvider(LLMProvider):
    """My new LLM provider implementation."""

    def _setup_provider(self) -> None:
        """Setup provider-specific configuration."""
        if self.config.api_key:
            os.environ["MY_PROVIDER_API_KEY"] = self.config.api_key
        elif not os.getenv("MY_PROVIDER_API_KEY"):
            raise ValueError("MY_PROVIDER_API_KEY must be set")

    def format_model_name(self, model: str) -> str:
        """Format model name for this provider."""
        # Add any provider-specific formatting
        return f"my-provider/{model}"
```

2. **Register the provider** in the `PROVIDER_REGISTRY`:

```python
PROVIDER_REGISTRY: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "anthropic": AnthropicProvider,
    "my-provider": MyNewProvider,  # Add your provider here
}
```

3. **Update documentation** to include the new provider.

## Architecture

The LLM provider system consists of:

- **`adt_press/llm/providers.py`**: Abstract base class and provider implementations
- **`adt_press/llm/__init__.py`**: Global provider management and helper functions
- **`adt_press/models/config.py`**: Configuration models for provider settings
- **`config/config.yaml`**: Default configuration file

All LLM modules automatically use the configured provider through the `format_model_name()` function, which ensures model names are correctly formatted for each provider.

## Troubleshooting

### API Key Not Found

Make sure the appropriate API key environment variable is set:

- OpenAI: `OPENAI_API_KEY`
- Gemini: `GEMINI_API_KEY`
- Anthropic: `ANTHROPIC_API_KEY`

### Model Not Found

Verify that:

1. The model name is correct for your provider
2. You have access to the model with your API key
3. The model name formatting is appropriate (check logs)

### Provider Not Supported

If you see "Unsupported provider" error, check that:

1. The provider name is spelled correctly (`openai`, `gemini`, `anthropic`)
2. The provider is registered in `PROVIDER_REGISTRY`

## Benefits

- **Flexibility**: Easily switch between providers without code changes
- **Extensibility**: Add new providers by implementing a simple interface
- **Cost Optimization**: Choose the most cost-effective model for your needs
- **Performance**: Use faster models when appropriate
- **Future-Proof**: Adapt to new LLM providers as they emerge
