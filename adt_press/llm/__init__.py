import os
from typing import Any

import litellm
import mlflow

from adt_press.llm.providers import LLMProvider, create_provider

# if langfuse is configured, set up callbacks for litellm
if os.getenv("LANGFUSE_HOST"):
    # set callbacks
    litellm.success_callback = ["langfuse"]
    litellm.failure_callback = ["langfuse"]

# if mlflow is configured, set up autologging
if os.getenv("MLFLOW_TRACKING_URI"):
    # Enable auto-tracing for LiteLLM
    mlflow.litellm.autolog()


# Global provider instance - initialized when first needed
_provider: LLMProvider | None = None


def get_provider() -> LLMProvider:
    """
    Get the global LLM provider instance.

    The provider is configured based on environment variables or defaults to OpenAI.
    Environment variables:
    - LLM_PROVIDER: Provider type (openai, gemini, anthropic)
    - OPENAI_API_KEY: For OpenAI provider
    - GEMINI_API_KEY: For Gemini provider
    - ANTHROPIC_API_KEY: For Anthropic provider
    - LLM_BASE_URL: Optional custom base URL for provider
    """
    global _provider
    if _provider is None:
        provider_type = os.getenv("LLM_PROVIDER", "openai").lower()
        _provider = create_provider(
            provider_type=provider_type,
            base_url=os.getenv("LLM_BASE_URL"),
        )
    return _provider


def set_provider(provider: LLMProvider) -> None:
    """Set the global LLM provider instance."""
    global _provider
    _provider = provider


def get_instructor_client(**kwargs: Any):
    """
    Return an Instructor-wrapped LiteLLM client that prefers JSON-schema modes.

    Uses the configured LLM provider to create the client.
    We try newer response-format modes first and gracefully fall back
    to the default Instructor behaviour if those are
    unavailable in the installed Instructor version.
    """
    provider = get_provider()
    return provider.get_instructor_client(**kwargs)


def format_model_name(model: str) -> str:
    """
    Format model name for the current provider.

    Args:
        model: Generic model name

    Returns:
        Provider-specific formatted model name
    """
    provider = get_provider()
    return provider.format_model_name(model)
