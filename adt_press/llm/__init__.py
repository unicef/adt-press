import os
from typing import Any

import litellm
import mlflow

from adt_press.llm.providers import LLMProvider

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

    The provider must be initialized via set_provider() before calling this function.
    This typically happens through the llm_provider_settings_config node in the pipeline.

    Raises:
        RuntimeError: If provider has not been initialized
    """
    global _provider
    if _provider is None:
        raise RuntimeError(
            "LLM provider not initialized. Ensure llm_provider is configured in config.yaml "
            "and the pipeline has initialized the provider via llm_provider_settings_config node."
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
