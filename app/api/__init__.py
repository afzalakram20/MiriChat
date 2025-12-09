from fastapi import APIRouter
 
from app.api.routers import horizon_routes
from app.api.routers import preprocess_router
from app.api.routers import summarization_routes


api_router = APIRouter()
api_router.include_router(horizon_routes.router)
api_router.include_router(preprocess_router.router)
api_router.include_router(summarization_routes.router)
