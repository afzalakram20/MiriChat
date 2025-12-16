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
        model_id = str(payload.get("model_id", "")).strip() or None
        model_key = str(payload.get("model_key", "")).strip() or None
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        if not chat_id:
            raise HTTPException(status_code=400, detail="Chat ID is required")
        
        if not model_id:
            raise HTTPException(status_code=400, detail="Model is required")
        if not model_key:
            raise HTTPException(status_code=400, detail="Model key is required")
        try:
            return await self.service.process_horizon_engine_request(query, chat_id, model_id, model_key)
        except Exception:
            log.exception("Dynamic processing failed")
            raise HTTPException(status_code=500, detail="Internal server error")
