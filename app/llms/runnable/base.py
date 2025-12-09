from __future__ import annotations

from abc import ABC
from typing import Any, Dict, List, Optional

from langchain_core.runnables import Runnable
from langchain_core.language_models.chat_models import BaseChatModel
 

import logging

log = logging.getLogger("app.models.llm.base")


class LLMError(Exception):
    """Generic LLM-related exception."""
    pass


 

class BaseLLM(Runnable, ABC):
    
    chat_model: BaseChatModel

    # ---------- Runnable interface ----------

    def invoke(
        self,
        input: Any,
        config: Optional[dict] = None,
        **kwargs: Any,
    ) -> Any:
        """Sync invoke: delegate to underlying chat_model."""
        return self.chat_model.invoke(input, config=config, **kwargs)

    async def ainvoke(
        self,
        input: Any,
        config: Optional[dict] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Async invoke: use chat_model.ainvoke if available,
        otherwise fall back to Runnable's default implementation.
        """
        ainvoke = getattr(self.chat_model, "ainvoke", None)
        if callable(ainvoke):
            return await ainvoke(input, config=config, **kwargs)  # type: ignore[arg-type]
        # Fallback (should rarely be needed)
        return await super().ainvoke(input, config=config, **kwargs)

    @property
    def runnable(self) -> BaseChatModel:
        """
        Direct access to the underlying `ChatModel` if you ever need it.
        Typically not needed, because BaseLLM itself is a Runnable.
        """
        return self.chat_model
 
 