from fastapi import Request
from fastapi.responses import JSONResponse
import structlog


log = structlog.get_logger()


async def unhandled_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", path=str(request.url), error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})