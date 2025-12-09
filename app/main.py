from contextlib import asynccontextmanager
 
from app.db.base import Base  # noqa: F401 - ensures models are registered
# from app.db.session import engine
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings 
from app.core.errors import unhandled_exception_handler
 
from app.mcp.server import start_mcp_server_if_needed
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routers.horizon_routes import router as horizon_router
from app.api.routers.preprocess_router import router as preprocess_router
from app.api.routers.summarization_routes import router as summarization_router
from app.api.routers.capital_plan_routes import router as capital_router
import os
setup_logging(settings.LOG_FILE_PATH, settings.LOG_LEVEL)
os.environ.pop("OPENAI_API_KEY", None)

 


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Create DB tables on startup (simple projects). Prefer migrations in production.
#     Base.metadata.create_all(bind=engine)
#     yield


app = FastAPI(title=settings.project_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(Exception, unhandled_exception_handler)

@app.on_event("startup")
async def on_startup():
    start_mcp_server_if_needed()
    # log.info("startup", env=settings.APP_ENV)

# Routers
# app.include_router(health.router)
app.include_router(horizon_router)
app.include_router(preprocess_router)
app.include_router(summarization_router)
app.include_router(capital_router)



if __name__ == "__main__":
    os.environ.pop("OPENAI_API_KEY", None)
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
