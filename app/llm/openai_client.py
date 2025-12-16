
from typing import Optional, Any, Dict, List
from openai import OpenAI, AsyncOpenAI
from app.core.config import settings
import logging

# Central logger for LLM prompts
_prompt_log = logging.getLogger("app.llm.prompt")

# Prefer async client for compatibility with async nodes if needed
_async_client: Optional[AsyncOpenAI] = None
_sync_client: Optional[OpenAI] = None


def _summarize_messages(messages: Any) -> List[Dict[str, Any]]:
    try:
        summarized: List[Dict[str, Any]] = []
        for m in messages or []:
            # Only include role and content to avoid logging large/unsupported fields
            summarized.append({
                "role": m.get("role"),
                "content": m.get("content"),
            })
        return summarized
    except Exception:
        return []


def _install_chat_logging(client: Any, is_async: bool = False) -> None:
    """Wrap chat.completions.create to log prompts before sending.

    Idempotent: safe to call multiple times.
    """
    try:
        chat = getattr(client, "chat", None)
        if chat is None:
            return
        completions = getattr(chat, "completions", None)
        if completions is None:
            return

        # Avoid double wrapping
        if getattr(completions, "_codex_prompt_wrapped", False):
            return

        original_create = getattr(completions, "create")

        if is_async:
            async def create_with_logging(*args, **kwargs):  # type: ignore
                model = kwargs.get("model")
                messages = kwargs.get("messages")
                temperature = kwargs.get("temperature")
                _prompt_log.info(
                    {
                        "event": "openai.chat.completions.create",
                        "model": model,
                        "temperature": temperature,
                        "messages": _summarize_messages(messages),
                    }
                )
                return await original_create(*args, **kwargs)
            setattr(completions, "create", create_with_logging)
        else:
            def create_with_logging(*args, **kwargs):  # type: ignore
                model = kwargs.get("model")
                messages = kwargs.get("messages")
                temperature = kwargs.get("temperature")
                _prompt_log.info(
                    {
                        "event": "openai.chat.completions.create",
                        "model": model,
                        "temperature": temperature,
                        "messages": _summarize_messages(messages),
                    }
                )
                return original_create(*args, **kwargs)
            setattr(completions, "create", create_with_logging)

        setattr(completions, "_codex_prompt_wrapped", True)
    except Exception as _e:
        # Swallow errors to avoid breaking runtime if SDK internals change
        _prompt_log.debug(f"Prompt logging wrap skipped: {_e}")

def get_sync_client() -> OpenAI:
    global _sync_client
    if _sync_client is None:
        _sync_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        _install_chat_logging(_sync_client, is_async=False)
    return _sync_client

def get_async_client() -> AsyncOpenAI:
    global _async_client
    if _async_client is None:
        _async_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        _install_chat_logging(_async_client, is_async=True)
    return _async_client
