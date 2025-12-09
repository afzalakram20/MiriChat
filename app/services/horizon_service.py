from app.graphs.horizon_brain_graph import build_horizon_brain_graph
import logging

log = logging.getLogger("app.services.horizon")


class HorizonService:
    async def process_horizon_engine_request(self, user_input: str) -> dict:

        graph = build_horizon_brain_graph()
        init_state = {"user_input": user_input}
        final_state = await graph.ainvoke(init_state)
        log.info(f"the final state--->{final_state}")

        if final_state.get("intent") == "work_request_generation":
            return {
                "user_input": final_state.get("user_input", ""),
                "work_request_payload": final_state["work_request_payload"],
                "human_summary_json": "",
            }
        if final_state.get("intent") == "text_to_sql":
            return {
                "user_input": final_state.get("user_input", ""),
                "rows_data": final_state["rows_data"],
                "human_summary_json": "",
            }

        if final_state.get("intent") == "project_summary":
            return {
                "user_input": final_state.get("user_input", ""),
                "project_summary_data": final_state["project_summary_data"],
                "human_summary_json": "",
            }

        # === Structured result with table rows ===
        # if final_state.get("rows") is not None:
        #     return {
        #         "row_count": final_state.get("row_count", 0),
        #         "rows": final_state["rows"],
        #         "exported": bool(final_state.get("export_path")),          # path-based export detection
        #         "emailed": bool(final_state.get("email_sent") or final_state.get("emailed")),
        #         "aggregate_summary": final_state.get("aggregate_summary"),
        #         "response": final_state.get("response"),
        #         "plan": final_state.get("plan"),
        #         "task_results": final_state.get("task_results"),
        #         # 👇 new AI-generated readable + dynamic summary
        #         "human_summary_json": final_state.get("human_summary_json"),
        #     }

        # === Text-based or fallback result (no rows) ===
        if final_state.get("response") or final_state.get("human_summary_json"):
            return {
                "message": final_state.get("response"),
                "aggregate_summary": final_state.get("aggregate_summary"),
                "plan": final_state.get("plan"),
                "task_results": final_state.get("task_results"),
                "human_summary_json": final_state.get("human_summary_json"),
            }

        # === Empty / default fallback ===
        return {
            "message": "No result produced.",
            "human_summary_json": final_state.get("human_summary_json"),
        }
