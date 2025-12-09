async def workflow_router_node(state):
    intent = state.get("intent")

    # map intents to workflow labels
    if intent == "work_request":
        return "work_request"

    if intent == "project_summary":
        return "project_summary"

    if intent == "project_metadata":
        return "project_metadata"

    if intent == "sql_query":
        return "sql_workflow"

    if intent in {"rag_query", "app_info"}:
        return "rag_workflow"

    return "irrelevant"
