import time
import os
from pymongo import MongoClient
from app.core.config import settings
import logging

log = logging.getLogger("app.memory.mongo")


class MongoChatMemory:
    def __init__(self):
        self.tool_name = os.getenv("TOOL_NAME", "EW")
        uri = settings.MONGODB_URI
        database_name = settings.MONGODB_DB
        self.enabled = bool(uri and database_name)

        log.info(f"Mongo URI: {uri} Database: {database_name} Tool: {self.tool_name} Mongo Enabled: {self.enabled}")

        self.collection = None
        if not self.enabled:
            return

        # Attempt to create client. Handle DNS/SRV failures gracefully by disabling Mongo.
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
            # Verify connectivity early to avoid runtime failures on first operation
            client.admin.command("ping")
            log.info("Connected to Mongo")
            self.collection = client[database_name][settings.MONGODB_COLLECTION]
        except Exception as e:
            log.warning("Disabling Mongo memory due to connection error: %s", e, exc_info=True)
            self.enabled = False
            self.collection = None

    def get_chat_id(self, chat_id: str) -> str:
        return chat_id
        return f"{chat_id}:{self.tool_name}"

    def save_message(self, chat_id: str, role: str, content: str, payload=None):
        if not self.enabled or self.collection is None:
            return
        chat_id = self.get_chat_id(chat_id)
        message_doc = {
            "role": role,
            "content": content,
            "timestamp": int(time.time()),
        }
        if payload is not None:
            message_doc["payload"] = payload
        self.collection.update_one(
            {"_id": chat_id},
            {
                "$setOnInsert": {"chat_id": chat_id, "tool": self.tool_name},
                "$push": {
                    "messages": message_doc
                },
            },
            upsert=True,
        )
        log.info(f"INSIDE SAVE_MESSAGE IN <== MONGO SERVICE ==> ({chat_id}) SAVED SUCCESSFULLY")

    def load_history(self, chat_id: str, limit: int = 20, include_payload: bool = False):
        if not self.enabled or self.collection is None:
            return []
        chat_id = self.get_chat_id(chat_id)
        doc = self.collection.find_one({"_id": chat_id})
        if not doc:
            return []
        messages = doc.get("messages", [])
        if limit:
            messages = messages[-limit:]
        if include_payload:
            return messages
        # Return only role/content
        slim = []
        for m in messages:
            role = m.get("role")
            content = m.get("content")
            if role is None or content is None:
                continue
            slim.append({"role": role, "content": content})
        return slim

    def delete_chat(self, chat_id: str):
        if not self.enabled or self.collection is None:
            return
        chat_id = self.get_chat_id(chat_id)
        self.collection.delete_one({"_id": chat_id})
