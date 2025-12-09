from __future__ import annotations

import logging
from typing import Optional, Dict, Any

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import AIMessage

from app.core.config import settings
from .base import BaseLLM, LLMError

log = logging.getLogger("app.models.llm.bedrock")


class BedrockProvider(BaseLLM):
    """
    LangChain-native AWS Bedrock provider using ChatBedrockConverse.

    No boto3. No manual prompt formatting.
    - Supports Llama 3 and Claude 3 via Bedrock
    - Accepts LangChain message lists or plain strings
    - Fully Runnable: prompt | llm | parser
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        try:
            mid = model_id or settings.BEDROCK_MODEL_ID
            region = settings.BEDROCK_REGION

        except AttributeError as e:
            raise LLMError("Missing Bedrock settings in config") from e

        temp = (
            temperature
            if temperature is not None
            else getattr(settings, "BEDROCK_TEMPERATURE", 0.0)
        )

        max_out = (
            max_tokens
            if max_tokens is not None
            else getattr(settings, "BEDROCK_MAX_TOKENS", None)
        )

        log.info(f"Initializing ChatBedrockConverse model_id={mid}")

        kwargs: Dict[str, Any] = {
            "model_id": mid,
            "region_name": region,
            "temperature": temp,
        }

        # Optional — configure API keys manually
        if getattr(settings, "BEDROCK_ACCESS_KEY", None):
            kwargs["aws_access_key_id"] = settings.BEDROCK_ACCESS_KEY
        if getattr(settings, "BEDROCK_SECRET_KEY", None):
            kwargs["aws_secret_access_key"] = settings.BEDROCK_SECRET_KEY

        if max_out is not None:
            kwargs["max_tokens"] = max_out

        # The LangChain ChatModel
        self.chat_model = ChatBedrockConverse(**kwargs)

    # Optional: semantic alias for clarity
    async def chat(self, messages, tools=None):
        cm = self.chat_model
        if tools:
            cm = cm.bind_tools(tools)
        resp = await cm.ainvoke(messages)
        return resp  # AIMessage

    async def complete(self, prompt: str) -> str:
        resp = await self.chat_model.ainvoke(prompt)
        return resp.content

    def bind_tools(self, tools: Sequence[BaseTool], **kwargs):
        """
        Allow `BedrockProvider().bind_tools([...])`
        by delegating to the underlying ChatBedrockConverse.
        Returns a Runnable chat model with tools bound.
        """
        return self.chat_model.bind_tools(tools, **kwargs)
