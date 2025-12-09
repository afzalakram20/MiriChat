from app.services.best_selection import call_best_selection_llm
import json
import logging
from typing import Dict, Any, List
from app.models.capital.cost_estimator import (
    ItemEstimate,
    MaterialExtractionResult,
    ScopeRequest,
    EstimationResponse,
)
from app.services.cost_estimator import CostEstimatorService, estimate_price_for_item
from fastapi import HTTPException

log = logging.getLogger("app.controllers.capital_palnning")

logger = logging.getLogger("app.controllers.capital")


class CapitalPlanningController:
    async def estimate_materials(self, req: ScopeRequest):
        try:
            log.info("entered into capital planning controller")
            # 1) LLM: extract purchase items from SoW
            service = CostEstimatorService()
            material_result: MaterialExtractionResult = (
                await service.llm_extract_materials(req)
            )
            log.info("material_result: %s", material_result)

            if not material_result.items:
                raise HTTPException(
                    status_code=400, detail="No purchasable items found in scope."
                )

            # 2) For each item, call Tavily and estimate price
            estimates: List[ItemEstimate] = []
            for item in material_result.items:
                estimate = estimate_price_for_item(item, req)
                estimates.append(estimate)
                log.info("final estimate: %s", estimate)
            log.info("final estimates to return: %s", estimates)

            selected_estimates = []
            for estimate in estimates:
                selected = call_best_selection_llm(estimate)
                selected_estimates.append(selected)

            log.info("selected estimates to return: %s", selected_estimates)

            return {
                "ok": True,
                "data": selected_estimates,
                "error": None,
            }

        except HTTPException as e:
            raise e
        except Exception as e:
            return {
                "ok": False,
                "data": None,
                "error": {
                    "code": "SERVER_ERROR",
                    "message": str(e),
                },
            }
