import logging
from fastapi import HTTPException
from app.services.horizon_service import HorizonService

log = logging.getLogger("app.controllers.horizon")


class HorizonController:
    def __init__(self):
        self.service = HorizonService()

    async def horizon_engine(self, payload: dict):
        query = str(payload.get("user_input", "")).strip()
        chat_id = str(payload.get("chat_id", "")).strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        if not chat_id:
            raise HTTPException(status_code=400, detail="Chat ID is required")
        try:
            return await self.service.process_horizon_engine_request(query, chat_id)
        except Exception:
            log.exception("Dynamic processing failed")
            raise HTTPException(status_code=500, detail="Internal server error")
