"""LLM Factory for Agent Nodes.

Provides a centralized way to instantiate LLM instances with support for
multiple providers (Google, Anthropic).
"""

from enum import Enum
from typing import Optional

from langchain_core.language_models import BaseChatModel

from api.core.config import settings
from api.core.logger import logger


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    GOOGLE = "google"
    ANTHROPIC = "anthropic"


def get_llm(
    provider: Optional[LLMProvider] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
) -> BaseChatModel:
    """Factory function to get LLM instance.

    Args:
        provider: LLM provider to use. Defaults to settings.LLM_PROVIDER
        model: Model name to use. Defaults to settings.LLM_MODEL
        temperature: Temperature for generation (0.0 - 1.0)

    Returns:
        BaseChatModel instance

    Raises:
        ValueError: If provider is unknown or API key is missing
    """
    # Use defaults from settings if not provided
    if provider is None:
        provider = LLMProvider(settings.LLM_PROVIDER)
    if model is None:
        model = settings.LLM_MODEL

    logger.info(
        f"🤖 Initializing LLM: provider={provider.value}, model={model}, temp={temperature}"
    )

    if provider == LLMProvider.GOOGLE:
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required for Google provider")

        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=settings.GOOGLE_API_KEY,
            max_output_tokens=2048,  # Increased for structured output
        )

    elif provider == LLMProvider.ANTHROPIC:
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")

        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model,
            temperature=temperature,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
        )

    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
