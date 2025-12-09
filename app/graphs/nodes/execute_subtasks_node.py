
from typing import Dict, Any, List
from app.services.sqlgen import generate_sql_from_question
from app.db.mysql import run_select

def execute_subtasks_node(state: Dict[str, Any]) -> Dict[str, Any]:
    plan = state.get("plan", {})
    subtasks: List[Dict[str, Any]] = plan.get("subtasks", [])
    results: List[Dict[str, Any]] = state.get("subtask_results", [])
    # simple sequential execution; honor declared order
    for task in subtasks:
        ttype = task.get("type")
        if ttype == "sql_query":
            question = task.get("question", "")
            # 1) Generate SQL
            # (generate_sql_from_question is async—however our current sqlgen service returns via async def but sync OpenAI call.
            # We can call it via anyio from a sync node if needed, but easier: re-implement quick path here synchronously by delegating to service through event loop if present.)
            import anyio
            sql = anyio.run(generate_sql_from_question, question)
            rows = run_select(sql)
            results.append({"task_id": task.get("id"), "sql": sql, "rows": rows, "row_count": len(rows)})
        elif ttype == "explain":
            # For now, skip or attach a placeholder
            results.append({"task_id": task.get("id"), "note": "explain not implemented"})
        else:
            # ignore non-exec tasks here (post actions handled later)
            results.append({"task_id": task.get("id"), "note": f"skipped type {ttype}"})
    return {**state, "subtask_results": results}
