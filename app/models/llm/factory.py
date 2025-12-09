from app.core.config import settings
from .openai_provider import OpenAIProvider
from .base import BaseLLM

from .bedrock_provider import BedrockProvider
import logging
log = logging.getLogger("app.models.llm.factory")

_instance: BaseLLM | None = None

def get_llm(llm_name: str | None = None) -> BaseLLM:
    global _instance
    log.info(f"llm_name from param----{llm_name}")
    
    if llm_name:
        if llm_name.lower() == "meta":
            return BedrockProvider()
        elif llm_name.lower() == "openai":
            return OpenAIProvider()
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_name}")

    # Default behavior: use singleton based on settings
    if _instance is None:
        provider = settings.LLM_PROVIDER.lower()
        log.info(f"provider name----{provider}")
        if provider == "openai":
            _instance = OpenAIProvider()
        elif provider == "meta":
            _instance = BedrockProvider()
        else:
            raise ValueError(f"Unsupported LLM provider in settings: {provider}")
    return _instance