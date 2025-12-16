from app.controllers.huggingface import HuggingFaceController
from fastapi import APIRouter
import logging
from app.controllers.horizon_controller import HorizonController
import os
from app.core.config import settings

log = logging.getLogger("horizon_routes")
_controller = HorizonController()
_hfController = HuggingFaceController()
router = APIRouter(prefix="/horizon", tags=["Horizon"])
LOG_FILE_PATH = settings.LOG_FILE_PATH


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/horizon-engine")
async def horizon_engine(payload: dict):
    if os.path.exists(LOG_FILE_PATH):
        open(LOG_FILE_PATH, "w").close()
    return await _controller.horizon_engine(payload)


@router.post("/load-models")
async def load_models(payload: dict):
    if os.path.exists(LOG_FILE_PATH):
        open(LOG_FILE_PATH, "w").close()
    return await _hfController.loadModels()
