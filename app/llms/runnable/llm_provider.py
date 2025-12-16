from app.llms.runnable.do_llama_provider import DOLlamaProvider
from typing import Optional
import logging

from app.core.config import settings
from .base import BaseLLM
from .openai_provider import OpenAIProvider
from .bedrock_provider import BedrockProvider

log = logging.getLogger("app.models.llm.factory")

_instance: Optional[BaseLLM] = None


def _build_provider(provider_key: str, model_id: Optional[str] = None) -> BaseLLM:
    """Internal helper to map provider key -> provider."""
    key = provider_key.lower()
    log.info("Building LLM provider for key=%s", key)

    if key == "openai":
        return OpenAIProvider(model_id=model_id)
    if key in {"do_serverless", "digitalocean", "digitalocean_llama", "gradient"}:
        return DOLlamaProvider(model_id=model_id)
    if key in {"bedrock", "bedrock_provider", "bedrock_llama"}:
        return BedrockProvider(model_id=model_id)

    raise ValueError(f"Unsupported LLM provider: {provider_key}")


def get_chain_llm(llm_name: Optional[str] = None, model_id: Optional[str] = None) -> BaseLLM:

    global _instance

    # If a model_id is provided OR explicit provider is given, build a fresh instance.
    if llm_name or model_id:
        # Backwards-compatible convenience: if a single string is passed but it's not a known
        # provider key, treat it as a model_id and use the configured provider.
        known_keys = {
            "openai", "do_serverless", "digitalocean", "digitalocean_llama", "gradient",
            "bedrock", "bedrock_provider", "bedrock_llama"
        }
        if llm_name and llm_name.lower() not in known_keys and model_id is None:
            model_id = llm_name
            provider_key = (settings.LLM_PROVIDER or "do_serverless")
            log.info("get_llm inferring provider=%s for model_id=%s", provider_key, model_id)
            return _build_provider(provider_key, model_id=model_id)

        provider_key = llm_name or (settings.LLM_PROVIDER or "do_serverless")

        # Normalize model_id: if it's missing or equals the provider key, use the provider default from settings.
        try:
            if not model_id or (isinstance(model_id, str) and model_id.lower() == provider_key.lower()):
                if provider_key == "openai":
                    model_id = getattr(settings, "OPENAI_MODEL", None)
                elif provider_key in {"do_serverless", "digitalocean", "digitalocean_llama", "gradient"}:
                    model_id = getattr(settings, "DO_MODEL_ID", None)
                elif provider_key in {"bedrock", "bedrock_provider", "bedrock_llama"}:
                    model_id = getattr(settings, "BEDROCK_MODEL_ID", None)
        except Exception:
            # Leave model_id as is if settings lookup fails; downstream will raise a clear error
            pass

        log.info("get_llm called with provider=%s, model_id=%s", provider_key, model_id)
        return _build_provider(provider_key, model_id=model_id)

    # Default singleton based on settings
    if _instance is None:
        provider = settings.LLM_PROVIDER or "do_serverless"
        log.info("Initializing default LLM provider from settings: %s", provider)
        _instance = _build_provider(provider)

    return _instance
