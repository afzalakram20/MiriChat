from fastapi import APIRouter
import logging
from app.controllers.capital_planning_controller import CapitalPlanningController
import os
from app.core.config import settings

log = logging.getLogger("capital_planning")
_controller = CapitalPlanningController()
router = APIRouter(prefix="/capital-planning", tags=["Capital"])
LOG_FILE_PATH = settings.LOG_FILE_PATH


 
@router.post("/cost_estimater")
async def cost_estimater(payload: dict):
    if os.path.exists(LOG_FILE_PATH):
        open(LOG_FILE_PATH, "w").close()
    log.info("capital plan route---")
    return await _controller.estimate_materials(payload)


 