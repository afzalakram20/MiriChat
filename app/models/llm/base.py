from __future__ import annotations
from abc import ABC, abstractmethod
from typing import AsyncGenerator
import re

class LLMError(Exception):
    """Generic LLM provider error."""
    pass

class BaseLLM(ABC):
    """
    Minimal async interface for LLM providers.

    Implementors must provide `complete()`. `stream()` has a sensible
    default (yield the full text in one chunk) but providers can override
    to perform true token streaming.
    """

    @abstractmethod
    async def complete(self, prompt: str) -> str:
        """Return a full completion for the given prompt.
        Should raise `LLMError` on provider-specific failures.
        """
        ...

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Default streaming: yield the full completion once.
        Providers may override to yield incremental tokens/chunks.
        """
        text = await self.complete(prompt)
        yield text

    # ---------- Common helpers useful across providers ----------
    _FENCE_RE = re.compile(r"^```[a-zA-Z]*?|```$", re.M)

    @staticmethod
    def strip_code_fences(text: str) -> str:
        """Remove markdown code fences that models sometimes include."""
        return BaseLLM._FENCE_RE.sub("", text.strip())

    @staticmethod
    def ensure_trailing_semicolon(sql: str) -> str:
        """Ensure SQL ends with a semicolon; no-op if already present."""
        sql = sql.strip()
        return sql if sql.endswith(";") else sql + ";"
      