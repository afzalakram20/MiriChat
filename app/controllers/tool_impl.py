# tool_impl.py
import os
import httpx
from typing import List, Dict, Any

LARAVEL_BASE_URL = "http://127.0.0.1:8003/horizon-extra-works/mcp/api/v1/"
# LARAVEL_BASE_URL = "https://stagingapi.horizoncenter.co/horizon-extra-works/mcp/api/v1/"
LARAVEL_API_KEY = os.getenv("LARAVEL_API_KEY", "changeme")  # store in env/secret
import logging

log = logging.getLogger("SQL_EXECUTION")
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "X-API-KEY": LARAVEL_API_KEY,  # implement this on Laravel side
}


async def call_laravel(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{LARAVEL_BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()


async def tool_get_schema(modules: List[str]) -> Dict[str, Any]:
    """
    Tool: getSchema → POST
    """
    return await call_laravel("schema", {"modules": modules})


async def tool_execute_sql(query: str) -> Dict[str, Any]:
    """
    Tool: executeSQL →
    """
    log.info(f"Executing SQL query: {query} in tool_execute_sql")
    return await call_laravel("execute-sql", {"query": query})


async def getProjectData(params: List[str]) -> Dict[str, Any]:

    return await call_laravel("projects_by_ref_ids", {"ref_ids": params})


async def tool_project_data(
    filters: Dict[str, Any] | None, limit: int | None
) -> Dict[str, Any]:
    """
    Tool: projectData → POST /api/projects
    """
    payload: Dict[str, Any] = {}
    if filters:
        payload["filters"] = filters
    if limit:
        payload["limit"] = limit
    return await call_laravel("/api/projects", payload)


async def send_email_via_api(email_to: str, state: dict):
    # TODO integrate Laravel email API
    return True


async def export_file_via_api(format: str, state: dict):
    # TODO integrate Laravel export
    return "/tmp/export.xlsx"


async def notify_via_api(channel: str, message: str, state: dict):
    return True


async def create_record_via_api(params: dict):
    return {"record_id": 123, "status": "created"}


async def save_generic_via_api(params: dict, state: dict):
    return {"saved": True}


async def webhook_call_via_api(url: str, params: dict, state: dict):
    return True
