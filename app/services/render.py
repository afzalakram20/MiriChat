from typing import Any, Dict, List

def _safe_str(v: Any) -> str:
    return "" if v is None else str(v)

def render_json_fallback(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds a dynamic, JSON-serializable summary for Angular rendering.
    """
    rows: List[Dict[str, Any]] = state.get("rows") or []
    plan = state.get("plan") or {}
    agg = state.get("aggregate_summary") or {}
    exported = bool(state.get("exported"))
    emailed = bool(state.get("emailed"))
    email_to = state.get("email_to")

    # --- Dynamic table building ---
    table = {}
    if rows:
        all_keys = []
        for r in rows:
            for k in r.keys():
                if k not in all_keys:
                    all_keys.append(k)
        table = {
            "headers": all_keys,
            "rows": [
                {k: _safe_str(r.get(k, "")) for k in all_keys}
                for r in rows
            ],
        }

    # --- Summary ---
    summary = {
        "total_rows": len(rows),
        "iteration": agg.get("iteration"),
        "completed": agg.get("completed"),
        "total_subtasks": agg.get("total_subtasks"),
        "rows_total": agg.get("rows_total"),
        "exported": exported,
        "emailed": emailed,
        "email_to": email_to,
    }

    # --- Plan info ---
    plan_info = {
        "summary": plan.get("plan_summary"),
        "subtasks": [
            {"id": s.get("id"), "type": s.get("type"), "question": s.get("question")}
            for s in (plan.get("subtasks") or [])
        ],
        "post_actions": plan.get("post_actions") or [],
    }

    return {
        "overview": state.get("user_input", "").strip() or "Generated report",
        "table": table,
        "summary": summary,
        "plan": plan_info,
        "notes": {
            "sql_reasoning": state.get("sql_reasoning"),
            "response": state.get("response"),
        },
    }
