from contextlib import asynccontextmanager

from app.db.base import Base  # noqa: F401 - ensures models are registered

# from app.db.session import engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import unhandled_exception_handler
from app.mcp.server import start_mcp_server_if_needed
from app.core.logging import setup_logging
from app.api.routers.horizon_routes import router as horizon_router
from app.api.routers.preprocess_router import router as preprocess_router
from app.api.routers.summarization_routes import router as summarization_router
from app.api.routers.capital_plan_routes import router as capital_router

import os
import asyncio
import uvicorn

# --- Logging / env cleanup ---
setup_logging(settings.LOG_FILE_PATH, settings.LOG_LEVEL)
os.environ.pop("OPENAI_API_KEY", None)

# If you ever want to use lifespan for DB init, you can uncomment & wire it:
# @asynccontextmanager
# async def lifespan(app: FastAPI):
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


# Health endpoint for RunPod (will be used on PORT_HEALTH)
@app.get("/ping")
async def ping():
    return {"status": "ok"}


# Routers
app.include_router(horizon_router)
app.include_router(preprocess_router)
app.include_router(summarization_router)
app.include_router(capital_router)


# ---------- RunPod entrypoint ----------
async def _run_uvicorn_servers():
    """
    Run two uvicorn servers:
      - one on PORT       (main traffic)
      - one on PORT_HEALTH (/ping health check)
    """
    # RunPod injects these; we fall back to settings.PORT or 8000 for safety.
    port = int(os.getenv("PORT", getattr(settings, "PORT", 8000)))
    health_port = int(os.getenv("PORT_HEALTH", port))

    config_main = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
    config_health = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=health_port,
        log_level="info",
    )

    server_main = uvicorn.Server(config_main)
    server_health = uvicorn.Server(config_health)

    # Run both servers concurrently
    await asyncio.gather(
        server_main.serve(),
        server_health.serve(),
    )


if __name__ == "__main__":
    # This block is what Docker will call via `python -m app.main`
    os.environ.pop("OPENAI_API_KEY", None)
    asyncio.run(_run_uvicorn_servers())
