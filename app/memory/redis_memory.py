import json
import time
import os
import redis
import logging

log = logging.getLogger("app.memory.redis")
from app.core.config import settings


class RedisChatMemory:
    def __init__(self, expiry_seconds: int = 7200):
        url = settings.REDIS_URL
        self.client = redis.StrictRedis.from_url(url)
        self.expiry = expiry_seconds
        self.tool_name = settings.TOOL_NAME or "EW"

    def get_key(self, chat_id: str) -> str:
        return chat_id
        return f"chat:{chat_id}:{self.tool_name}"

    def save_message(self, chat_id: str, role: str, content: str) -> None:
        try:
            key = self.get_key(chat_id)
            entry = {"role": role, "content": content, "timestamp": int(time.time())}
            self.client.rpush(key, json.dumps(entry))
            self.client.expire(key, self.expiry)
            log.info(f"INSIDE SAVE_MESSAGE IN <== REDIS SERVICE ==> ({key}) SAVED SUCCESSFULLY")
        except Exception:
            # Redis not running or unreachable -> ignore
            pass

    def load_history(self, chat_id: str, limit: int = 20, include_payload: bool = False):
        try:
            key = self.get_key(chat_id)
            messages = self.client.lrange(key, -limit, -1)
            parsed = []
            for m in messages:
                try:
                    entry = json.loads(m)
                except Exception:
                    continue
                if include_payload:
                    parsed.append(entry)
                else:
                    parsed.append({"role": entry.get("role"), "content": entry.get("content")})
            return parsed
        except Exception:
            return []

    def clear_memory(self, chat_id: str) -> None:
        try:
            self.client.delete(self.get_key(chat_id))
        except Exception:
            pass

    def write_history(self, chat_id: str, messages) -> None:
        try:
            key = self.get_key(chat_id)
            pipe = self.client.pipeline()
            pipe.delete(key)
            for m in messages:
                pipe.rpush(key, json.dumps(m))
            pipe.expire(key, self.expiry)
            pipe.execute()
        except Exception:
            pass
