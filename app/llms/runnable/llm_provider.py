from __future__ import annotations

from typing import Optional
import logging

from app.core.config import settings
from .base import BaseLLM
from .openai_provider import OpenAIProvider
from .bedrock_provider import BedrockProvider

log = logging.getLogger("app.models.llm.factory")

_instance: Optional[BaseLLM] = None


def _build_provider(provider_key: str) -> BaseLLM:
    """Internal helper to map provider key -> provider."""
    key = provider_key.lower()
    log.info("Building LLM provider for key=%s", key)

    if key == "openai":
        return OpenAIProvider()

    # Your existing config uses "meta" for Llama via Bedrock;
    # you can also support aliases like "bedrock" / "llama" here.
    if key in {"meta", "bedrock", "llama"}:
        return BedrockProvider()

    raise ValueError(f"Unsupported LLM provider: {provider_key}")


def get_chain_llm(llm_name: Optional[str] = None) -> BaseLLM:

    global _instance

    # Explicit provider → no singleton, useful when you want multiple models.
    if llm_name:
        log.info("get_llm called with explicit llm_name=%s", llm_name)
        return _build_provider(llm_name)

    # Default singleton based on settings
    if _instance is None:
        provider = settings.LLM_PROVIDER
        log.info("Initializing default LLM provider from settings: %s", provider)
        _instance = _build_provider(provider)

    return _instance
