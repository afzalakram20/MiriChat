from app.memory.mongo_memory import MongoChatMemory
from app.memory.redis_memory import RedisChatMemory
import logging
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage

log = logging.getLogger("app.memory.manager")


class MemoryManager:
    def __init__(self):
        self.mongo = MongoChatMemory()
        self.redis = RedisChatMemory()

    def save(self, chat_id, role, content, payload=None):
        # Persist to Mongo (source of truth, payload supported)
        try:
            self.mongo.save_message(chat_id, role, content, payload)
            log.info(f"Saved to Mongo ({chat_id}) Ran")
        except Exception as e:
            log.warning("Mongo save failed: %s", e, exc_info=True)
        # Cache to Redis (no payload)
        try:
            self.redis.save_message(chat_id, role, content)
            log.info(f"Saved to Redis ({chat_id}) Ran")
        except Exception:
            pass

    def load_context(self, chat_id, limit=20):
        # Try Redis first (fast)
        try:
            cached = self.redis.load_history(chat_id, limit, include_payload=False)
            if cached:
                log.info(f"Loaded from Redis ({chat_id})")
                return cached
        except Exception:
            pass

        # Fallback to Mongo (source of truth)
        try:
            log.info(f"Loading full history from Mongo ({chat_id})")
            full_history = self.mongo.load_history(chat_id, limit=limit, include_payload=False)
        except Exception:
            full_history = []

        if not full_history:
            return []

        recent = full_history  # already limited/slimmed by Mongo

        # Best-effort: repopulate Redis
        try:
            self.redis.write_history(chat_id, recent)
        except Exception:
            pass

        return recent

    def load_context_messages(self, chat_id, limit=20) -> list[BaseMessage]:
        """
        Returns recent conversation as LangChain message objects (HumanMessage/AIMessage).
        Falls back to an empty list on error.
        """
        raw = self.load_context(chat_id, limit=limit) or []
        messages: list[BaseMessage] = []
        for m in raw[-limit:]:
            try:
                role = (m.get("role") or "").strip().lower()
                content = str(m.get("content") or "")
            except Exception:
                continue
            if not content:
                continue
            if role == "assistant":
                messages.append(AIMessage(content))
            elif role == "user":
                messages.append(HumanMessage(content))
        return messages
    def load_full(self, chat_id):
        try:
            return self.mongo.load_history(chat_id, limit=0, include_payload=True)
        except Exception:
            return []
