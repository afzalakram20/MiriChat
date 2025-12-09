from __future__ import annotations

import logging
from typing import Optional, Sequence, Any, Dict

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage

from app.core.config import settings
from .base import BaseLLM, LLMError

log = logging.getLogger("app.models.llm.openai")


class OpenAIProvider(BaseLLM):
    """
    OpenAI provider aligned with BedrockProvider.

    Uses LangChain's ChatOpenAI so that:
    - self.chat_model exists
    - .invoke/.ainvoke work
    - tools binding works
    - fully compatible with LangGraph pipelines
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        try:
            mid = model_id or settings.OPENAI_MODEL
        except AttributeError as e:
            raise LLMError("Missing OPENAI_MODEL setting") from e

        # 🔑 Get API key from settings (or fail fast)
        api_key = getattr(settings, "OPENAI_API_KEY", None)
        if not api_key:
            raise LLMError(
                "OPENAI_API_KEY is not set in settings. "
                "Either set settings.OPENAI_API_KEY or the OPENAI_API_KEY env var."
            )

        temp = (
            temperature
            if temperature is not None
            else getattr(settings, "OPENAI_TEMPERATURE", 1)
        )

        max_out = (
            max_tokens
            if max_tokens is not None
            else getattr(settings, "OPENAI_MAX_TOKENS", None)
        )

        log.info(f"Initializing OpenAI ChatOpenAI model_id={mid}")

        kwargs: Dict[str, Any] = {
            "model": mid,
            "temperature": temp,
            "api_key": api_key,  # ✅ tell ChatOpenAI which key to use
        }

        if max_out is not None:
            kwargs["max_tokens"] = max_out

        # critical: BaseLLM needs this attribute
        self.chat_model = ChatOpenAI(**kwargs)

    async def chat(self, messages, tools: Sequence[Any] | None = None):
        cm = self.chat_model
        if tools:
            cm = cm.bind_tools(tools)

        resp = await cm.ainvoke(messages)
        return resp  # AIMessage

    async def complete(self, prompt: str) -> str:
        resp = await self.chat_model.ainvoke([{"role": "user", "content": prompt}])
        return resp.content or ""

    def bind_tools(self, tools: Sequence[Any], **kwargs):
        return self.chat_model.bind_tools(tools, **kwargs)
