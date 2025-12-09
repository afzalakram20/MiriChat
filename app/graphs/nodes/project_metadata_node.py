import json

async def project_metadata_node(state):
    from app.controllers.tool_impl import tool_project_data
    result = await tool_project_data({}, 20)
    state["response"] = json.dumps(result, indent=2)
    return state
