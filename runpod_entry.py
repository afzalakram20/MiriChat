import asyncio
import os
import uvicorn

# Read ports from RunPod environment
PORT = int(os.getenv("PORT", "8000"))
PORT_HEALTH = int(os.getenv("PORT_HEALTH", PORT))  # fallback to main port if not set


async def main():
    """
    Start two uvicorn servers:
    - one on PORT       → main traffic
    - one on PORT_HEALTH → for RunPod health checks (/ping)
    Both use the same FastAPI app: app.main:app
    """
    config_main = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=PORT,
        log_level="info",
    )
    server_main = uvicorn.Server(config_main)

    config_health = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=PORT_HEALTH,
        log_level="info",
    )
    server_health = uvicorn.Server(config_health)

    await asyncio.gather(
        server_main.serve(),
        server_health.serve(),
    )


if __name__ == "__main__":
    asyncio.run(main())
