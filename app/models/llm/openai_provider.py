from app.llm.openai_client import get_sync_client
from app.core.config import settings
from .base import BaseLLM
import logging
log = logging.getLogger("app.services.sqlchat")

class OpenAIProvider(BaseLLM):
    def __init__(self):  
        # Use shared client with centralized prompt logging
        self.client = get_sync_client()
        self.model = settings.OPENAI_MODEL

    async def complete(self, messages: list[dict], tools: list | None = None) -> str:
        
        resp =   self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
        )
        return resp.choices[0].message.content or ""
    
    async def chat(self, messages: list[dict], tools: list | None = None):
        """
        Chat-style API with messages + optional tools.
        Returns the raw OpenAI response so callers can inspect tool_calls, etc.
        """
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
        )
        return resp
