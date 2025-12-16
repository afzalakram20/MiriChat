from app.graphs.horizon_brain_graph import build_horizon_brain_graph
from typing import Any, Dict, List, Optional
import json
from app.memory.memory_manager import MemoryManager
import logging
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage

log = logging.getLogger("app.services.horizon")


class HorizonService:
    def __init__(self):
        self.memory_manager = MemoryManager()
        self.chat_id = None

    async def process_horizon_engine_request(self, user_input: str, chat_id: str, model_id: str | None = None, model_key: str | None = None) -> dict:
        self.chat_id = chat_id

        # Build structured chat history (latest last) via memory manager helper
        chat_history = self.memory_manager.load_context_messages(self.chat_id, limit=6)
        
        # Save user input
        try:
            self.memory_manager.save(self.chat_id, "user", user_input)
            log.info(f"Memory Save With Role User Succeeded: {user_input}")
        except Exception as e:
            log.warning(f"Memory Save With Role User Failed: {e}")

        # GRAPH ENGINE
        graph = build_horizon_brain_graph()

        init_state = {
            "user_input": user_input,
            "chat_history": chat_history,
            "chat_id": self.chat_id,
            "model_id": model_id,
            "model_key": model_key,
        }

        log.info(f"the init state--->{init_state}")
        final_state = await graph.ainvoke(init_state)
        log.info(f"the final state--->{final_state}")

        try:
            assistant_text = self._get_assistant_text(final_state)

            payload_data = self._get_payload(final_state)

            if assistant_text:
                self.memory_manager.save(self.chat_id, "assistant", assistant_text, payload=payload_data)
        except Exception as e:
            log.warning(f"Memory Save (Assistant Exact Response) Failed: {e}")

        if final_state.get("intent") == "work_request_generation":
            return {
                "user_input": final_state.get("user_input", ""),
                "work_request_payload": final_state["work_request_payload"],
                "type": "work_request_generation",
                "human_summary_json": ""
            }
        if final_state.get("intent") == "text_to_sql":
            return {
                "user_input": final_state.get("user_input", ""),
                "rows_data": final_state["rows_data"],
                "human_summary_json": ""
            }

        if final_state.get("intent") == "project_summary":
            return {
                "user_input": final_state.get("user_input", ""),
                "project_summary_data": final_state["project_summary_data"],
                "type": "project_summary",
                "human_summary_json": ""
            }
        if final_state.get("intent") == "app_info" or final_state.get("intent") == "rag_query":
            return {
                "user_input": final_state.get("user_input", "") or "",
                "message": final_state.get("response") or "",
                "type": "app_info",
                "human_summary_json": ""
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
                "human_summary_json": final_state.get("human_summary_json")
            }

        # === Empty / default fallback ===
        return {
            "message": "No result produced.",
            "human_summary_json": final_state.get("human_summary_json")
        }

    def _get_assistant_text(self, final_state: Dict[str, Any]) -> str:
        # Prefer intent-specific, reliable fields first to avoid fallback messages
        intent = (final_state.get("intent") or "").lower()

        if intent == "app_info":
            return str(final_state.get("response") or final_state.get("message") or "")

        if intent == "text_to_sql" and final_state.get("sql") is not None:
            try:
                return json.dumps(final_state.get("sql"), ensure_ascii=False)
            except Exception:
                return str(final_state.get("sql"))

        if intent == "work_request_generation" and final_state.get("work_request_payload") is not None:
            try:
                return json.dumps(final_state.get("work_request_payload"), ensure_ascii=False)
            except Exception:
                return str(final_state.get("work_request_payload"))

        if intent == "project_summary" and final_state.get("project_summary_data") is not None:
            try:
                return json.dumps(final_state.get("project_summary_data"), ensure_ascii=False)
            except Exception:
                return str(final_state.get("project_summary_data"))

        # Next, try human_summary_json if available
        human_summary = final_state.get("human_summary_json")
        if isinstance(human_summary, dict):
            text = human_summary.get("summary_text") or (human_summary.get("notes") or {}).get("response")
            if text:
                return text
        elif isinstance(human_summary, str) and human_summary:
            return human_summary

        # Fallback to generic response/message
        return str(final_state.get("response") or final_state.get("message") or "")

    def _get_payload(self, final_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        intent_for_payload = (final_state.get("intent") or "").lower()
        payload_value = None
        if (
                intent_for_payload == "text_to_sql"
                and final_state.get("rows_data") is not None
        ):
            payload_value = final_state.get("rows_data")
        elif (
                intent_for_payload == "work_request_generation"
                and final_state.get("work_request_payload") is not None
        ):
            payload_value = final_state.get("work_request_payload")
        elif (
                intent_for_payload == "project_summary"
                and final_state.get("project_summary_data") is not None
        ):
            payload_value = final_state.get("project_summary_data")
        elif intent_for_payload == "app_info":
            payload_value = final_state.get("response")

        if payload_value is not None and intent_for_payload:
            return {"intent": intent_for_payload, "data": payload_value}
        return {"intent": intent_for_payload, "data": {}}
