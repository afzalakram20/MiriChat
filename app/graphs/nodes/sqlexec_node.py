# Executes SQL (readonly). Keep your safety checks inside service/db layer.

# from app.db.mysql import run_select

# def sqlexec_node(state: dict) -> dict:
#     sql = state.get("sql")
#     rows = run_select(sql)
#     return {**state, "rows": rows, "row_count": len(rows)}


from app.controllers.tool_impl import tool_execute_sql
import logging

log = logging.getLogger("SQL_EXECUTION")


async def sqlexec_node(state: dict) -> dict:
    sql = state.get("sql")
    log.info(f"sql execution node received ---> {sql}")

    result = await tool_execute_sql(sql)
    log.info(f"sql execution rows executed ---> {result}")

    # Normalize result into list of rows
    if isinstance(result, dict):
        if "rows" in result:
            rows = result["rows"]
        elif "data" in result:
            rows = result["data"]
        else:
            # unexpected dict structure → treat values as records
            rows = list(result.values())
    else:
        rows = result  # already a list
    state["rows_data"] = rows
    return state
    # if not isinstance(rows, list):
    #     log.warning(f"Rows are not a list, converting to list: {rows}")
    #     rows = [rows]

    # return {**state, "rows": rows, "row_count": len(rows)}
