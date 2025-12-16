"""
LLM Provider abstraction layer for supporting multiple LLM backends.

This module provides a unified interface for different LLM providers (OpenAI, Gemini, Claude, etc.)
while leveraging LiteLLM for the actual API calls. The abstraction allows easy switching between
providers and consistent handling of provider-specific configurations.
"""

import os
from abc import ABC, abstractmethod
from typing import Any

import instructor
from litellm import acompletion

from adt_press.utils.encoding import CleanTextBaseModel


class LLMProviderConfig(CleanTextBaseModel):
    """Base configuration for LLM providers."""

    provider_type: str
    api_key: str | None = None
    base_url: str | None = None
    default_model: str | None = None
    extra_params: dict[str, Any] = {}


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Each provider implementation handles:
    - Model name formatting (e.g., "gpt-4" vs "gemini/gemini-pro")
    - API key management
    - Provider-specific parameters
    - Instructor client creation
    """

    def __init__(self, config: LLMProviderConfig):
        self.config = config
        self._setup_provider()

    @abstractmethod
    def _setup_provider(self) -> None:
        """Setup provider-specific configuration (API keys, callbacks, etc.)."""
        pass

    @abstractmethod
    def format_model_name(self, model: str) -> str:
        """
        Format the model name for the specific provider.

        Args:
            model: Generic model name (e.g., "gpt-4", "gemini-pro")

        Returns:
            Provider-specific model name (e.g., "gpt-4" for OpenAI, "gemini/gemini-pro" for Gemini)
        """
        pass

    def get_instructor_client(self, **kwargs: Any) -> instructor.Instructor:
        """
        Return an Instructor-wrapped LiteLLM client for structured outputs.

        Tries newer response-format modes first and gracefully falls back
        to the default Instructor behavior if those are unavailable.
        """
        mode_candidates = [
            "JSON_SCHEMA",
            "JSON",
            "OPENAI_RESPONSE_FORMAT",
        ]

        for attr in mode_candidates:
            mode = getattr(instructor.Mode, attr, None)
            if mode is not None:
                return instructor.from_litellm(acompletion, mode=mode, **kwargs)

        return instructor.from_litellm(acompletion, **kwargs)

    async def create_completion(self, model: str, **kwargs: Any) -> Any:
        """
        Create a completion using LiteLLM with provider-specific formatting.

        Args:
            model: Model name to use
            **kwargs: Additional parameters to pass to litellm.acompletion

        Returns:
            LiteLLM completion response
        """
        formatted_model = self.format_model_name(model)
        return await acompletion(model=formatted_model, **kwargs)


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation."""

    def _setup_provider(self) -> None:
        """Setup OpenAI-specific configuration."""
        if self.config.api_key:
            os.environ["OPENAI_API_KEY"] = self.config.api_key
        elif not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY must be set either in config or environment")

        # Set base URL if provided (for Azure OpenAI or custom endpoints)
        if self.config.base_url:
            os.environ["OPENAI_API_BASE"] = self.config.base_url

    def format_model_name(self, model: str) -> str:
        """
        Format model name for OpenAI.

        OpenAI models don't need a prefix in LiteLLM.
        Examples: "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"
        """
        return model


class GeminiProvider(LLMProvider):
    """Google Gemini provider implementation."""

    def _setup_provider(self) -> None:
        """Setup Gemini-specific configuration."""
        if self.config.api_key:
            os.environ["GEMINI_API_KEY"] = self.config.api_key
        elif not os.getenv("GEMINI_API_KEY"):
            raise ValueError("GEMINI_API_KEY must be set either in config or environment")

    def format_model_name(self, model: str) -> str:
        """
        Format model name for Gemini.

        LiteLLM requires Gemini models to be prefixed with "gemini/"
        Examples: "gemini/gemini-pro", "gemini/gemini-1.5-pro"
        """
        if not model.startswith("gemini/"):
            # Handle common model name variations
            if model.startswith("gemini-"):
                return f"gemini/{model}"
            else:
                # Assume it's a gemini model shorthand (e.g., "pro", "1.5-pro")
                return f"gemini/gemini-{model}"
        return model


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation."""

    def _setup_provider(self) -> None:
        """Setup Anthropic-specific configuration."""
        if self.config.api_key:
            os.environ["ANTHROPIC_API_KEY"] = self.config.api_key
        elif not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY must be set either in config or environment")

    def format_model_name(self, model: str) -> str:
        """
        Format model name for Anthropic Claude.

        LiteLLM requires Claude models to be prefixed with "claude-"
        Examples: "claude-3-5-sonnet-20241022", "claude-3-opus-20240229"
        """
        if not model.startswith("claude-"):
            # Add prefix if not present
            return f"claude-{model}"
        return model


# Provider registry mapping provider types to their implementations
PROVIDER_REGISTRY: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "anthropic": AnthropicProvider,
}


def create_provider(provider_type: str, **config_kwargs: Any) -> LLMProvider:
    """
    Factory function to create a provider instance.

    Args:
        provider_type: Type of provider ("openai", "gemini", "anthropic")
        **config_kwargs: Configuration parameters for the provider

    Returns:
        Configured LLMProvider instance

    Raises:
        ValueError: If provider_type is not supported
    """
    if provider_type not in PROVIDER_REGISTRY:
        raise ValueError(f"Unsupported provider: {provider_type}. Supported providers: {list(PROVIDER_REGISTRY.keys())}")

    provider_class = PROVIDER_REGISTRY[provider_type]
    config = LLMProviderConfig(provider_type=provider_type, **config_kwargs)
    return provider_class(config)
