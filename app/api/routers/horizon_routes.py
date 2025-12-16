from app.controllers.huggingface import HuggingFaceController
from fastapi import APIRouter
import logging
from app.controllers.horizon_controller import HorizonController
import os
from app.core.config import settings
from fastapi.responses import StreamingResponse, FileResponse, Response
import asyncio
import json

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


@router.post("/horizon-engine/stream")
async def horizon_engine_stream(payload: dict):
    """
    Server-Sent Events (SSE) stream that yields assistant text progressively,
    similar to ChatGPT streaming. It streams the final message in small chunks.
    """
    if os.path.exists(LOG_FILE_PATH):
        open(LOG_FILE_PATH, "w").close()

    async def chunk_stream():
        try:
            # Kick off the heavy work in the background so we can stream keep-alives
            task = asyncio.create_task(_controller.horizon_engine(payload))

            # Send invisible SSE comment heartbeats while computation runs.
            # Clients won't render these lines, but they keep proxies/connections alive.
            while not task.done():
                yield ": keep-alive\n\n"
                await asyncio.sleep(0.75)

            # Fetch the actual result
            result = await task

            # Stream the EXACT response structure as JSON, in chunks.
            try:
                text = json.dumps(result, ensure_ascii=False)
            except Exception:
                text = str(result)

            chunk_size = 256
            for i in range(0, len(text), chunk_size):
                delta = text[i : i + chunk_size]
                yield f"data: {json.dumps({'delta': delta})}\n\n"
                await asyncio.sleep(0)  # yield to loop

            yield "data: {\"done\": true}\n\n"
        except Exception as e:
            err = {"error": str(e)}
            yield f"data: {json.dumps(err)}\n\n"
            yield "data: {\"done\": true}\n\n"

    return StreamingResponse(
        chunk_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # Helpful if behind proxies like Nginx
            "X-Accel-Buffering": "no",
        },
    )



@router.post("/load-models")
async def load_models(payload: dict):
    if os.path.exists(LOG_FILE_PATH):
        open(LOG_FILE_PATH, "w").close()
    return await _hfController.loadModels()


@router.get("/stream-test", include_in_schema=False)
async def stream_test_page():
    # Serve the static HTML page for manual streaming tests (robust path resolution)
    try:
        from pathlib import Path
        base_dir = Path(__file__).resolve().parent
        cand1 = (base_dir / ".." / ".." / "web" / "stream_test.html").resolve()
        if cand1.exists():
            return FileResponse(str(cand1), media_type="text/html")
        # Fallback to CWD-based path (useful in some dev setups)
        cand2 = (Path.cwd() / "app" / "web" / "stream_test.html").resolve()
        if cand2.exists():
            return FileResponse(str(cand2), media_type="text/html")
    except Exception:
        pass
    # Last resort: tiny inline page to point user
    return Response(
        content=(
            "<!doctype html><html><body>"
            "<p>stream_test.html not found. "
            "Ensure it exists at app/web/stream_test.html.</p>"
            "<p>Expected URL: /horizon/horizon-engine/stream</p>"
            "</body></html>"
        ),
        media_type="text/html",
    )


