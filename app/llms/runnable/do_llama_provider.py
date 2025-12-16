from __future__ import annotations

import logging
from typing import Optional, Dict, Any, Sequence

from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage

from app.core.config import settings
from .base import BaseLLM, LLMError

log = logging.getLogger("app.models.llm.do_llama")


class DOLlamaProvider(BaseLLM):
    """
    DigitalOcean (Gradient) Serverless Inference provider.

    DigitalOcean Serverless Inference is OpenAI-compatible:
    - Base URL: https://inference.do-ai.run/v1
    - Auth: Authorization: Bearer <MODEL_ACCESS_KEY>

    This provider uses LangChain's ChatOpenAI with a custom base_url.
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        try:
            # Required
            log.info("Initializing DigitalOcean Serverless Inference model_id=%s base_url=%s", model_id, base_url)
            do_key = api_key or getattr(settings, "DO_MODEL_ACCESS_KEY")
            if not do_key:
                raise LLMError("Missing DO_MODEL_ACCESS_KEY in settings")

            # Optional / defaults
            mid = model_id or getattr(settings, "DO_MODEL_ID", None)
            if not mid:
                raise LLMError("Missing DO_MODEL_ID in settings (e.g., llama3.3-70b-instruct)")

            url = base_url or getattr(settings, "DO_INFERENCE_BASE_URL", "https://inference.do-ai.run/v1")

        except AttributeError as e:
            raise LLMError("Missing DigitalOcean settings in config") from e

        temp = temperature if temperature is not None else getattr(settings, "DO_TEMPERATURE", 0.0)
        max_out = max_tokens if max_tokens is not None else getattr(settings, "DO_MAX_TOKENS", None)
        req_timeout = timeout if timeout is not None else getattr(settings, "DO_TIMEOUT", 120.0)

        log.info("Initializing DigitalOcean Serverless Inference model_id=%s base_url=%s", mid, url)

        kwargs: Dict[str, Any] = {
            "model": mid,
            "api_key": do_key,
            "base_url": url,
            "temperature": temp,
            "timeout": req_timeout,
        }

        # Only pass max_tokens if explicitly set; some backends are picky.
        if max_out is not None:
            kwargs["max_tokens"] = max_out

        # LangChain ChatModel (OpenAI-compatible)
        self.chat_model = ChatOpenAI(**kwargs)

    async def chat(self, messages: Sequence[BaseMessage], tools: Optional[Sequence[BaseTool]] = None):
        """
        Chat with LangChain message objects. Returns an AIMessage.
        """
        log.info("Chat method called with model: %s messages: %s, tools: %s", self.chat_model, messages, tools)
        cm = self.chat_model
        if tools:
            cm = cm.bind_tools(tools)

        resp = await cm.ainvoke(messages)
        return resp

    async def complete(self, prompt: str) -> str:
        """
        Convenience method: plain string prompt.
        """
        resp = await self.chat_model.ainvoke(prompt)
        return resp.content

    def bind_tools(self, tools: Sequence[BaseTool], **kwargs):
        """
        Allow `DOLlamaProvider().bind_tools([...])` by delegating to ChatOpenAI.
        Returns a Runnable chat model with tools bound.
        """
        return self.chat_model.bind_tools(tools, **kwargs)

