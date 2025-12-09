from pydantic.main import BaseModel
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


class AutoProjectRequest(BaseModel):
    user_command: str


@router.post("/auto-generate-request")
async def auto_generate_project(payload: AutoProjectRequest):
    if os.path.exists(LOG_FILE_PATH):
        open(LOG_FILE_PATH, "w").close()
    log.info("capital plan route request---")
    try:
        result = _controller.analyze_project_command(payload.user_command)
        return result
    except ValueError as e:
        # for example invalid capacity pair
        log.error("ValueError: %s", e)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # log error, return safe message
        log.error("Exception: %s", e)
        raise HTTPException(status_code=500, detail="Failed to auto-generate project")
