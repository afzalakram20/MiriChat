# Placeholder: in real MCP you'd spin up an MCP server process exposing tools over stdio/WebSocket.
# For dev, we provide module-level functions directly and optional init hooks.


def start_mcp_server_if_needed():
    # No-op in dev; log hook could be added here.
    return True
