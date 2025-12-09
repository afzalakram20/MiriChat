from typing import List, Dict
from app.mcp.tools.projects import list_top_projects


# In real MCP, you'd connect via stdio/websocket.
# For dev, we call the function directly.


def mcp_list_top_projects(tenant: str, limit: int = 10) -> List[Dict]:
    return list_top_projects(tenant=tenant, limit=limit)