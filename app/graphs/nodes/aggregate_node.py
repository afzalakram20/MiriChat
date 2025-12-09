from typing import Dict, Any, List

def aggregate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    plan = state.get("plan", {}) or {}
    subs: List[Dict[str, Any]] = plan.get("subtasks", []) or []
    results: List[Dict[str, Any]] = state.get("task_results", []) or []
    iteration = int(state.get("iteration", 0))

    summary = {
        "iteration": iteration + 1,
        "total_subtasks": len(subs),
        "completed": len(results),
        "rows_total": sum(r.get("row_count", 0) for r in results if r.get("type") == "sql_query"),
    }

    # 🧠 NEW: extract post_actions and flags
    post_actions = plan.get("post_actions", []) or []

    export = state.get("export", False) or any(a.get("type") == "export" for a in post_actions)
    email = state.get("email", False) or any(a.get("type") in {"email", "send_email"} for a in post_actions)

    email_to = state.get("email_to")
    if not email_to:
        for a in post_actions:
            if a.get("type") in {"email", "send_email"}:
                email_to = (
                    a.get("params", {}).get("email_to")
                    or a.get("params", {}).get("to")
                    or email_to
                )

    plan["follow_up"] = plan.get("follow_up", False)

    response = state.get("response") or f"Completed {len(results)}/{len(subs)} subtasks."

    new_state = {
        **state,
        "aggregate_summary": summary,
        "iteration": iteration + 1,
        "plan": plan,
        "export": export,
        "email": email,
        "email_to": email_to,  # ✅ ensures email_to exists
        "response": response,
    }

    # (optional legacy SQL data pass-through)
    first_sql = next((r for r in results if r.get("type") == "sql_query"), None)
    if first_sql:
        new_state["rows"] = first_sql.get("rows")
        new_state["row_count"] = first_sql.get("row_count")

    return new_state
