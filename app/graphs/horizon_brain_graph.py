# app/graphs/horizon_brain_graph.py

from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END

# Core LLM nodes
from app.graphs.nodes.intent_node import intent_node
from app.graphs.nodes.planner_node import planner_node

# Execution nodes (SQL)
from app.graphs.nodes.sqlgen_node import sqlgen_node
from app.graphs.nodes.sqlexec_node import sqlexec_node

# Multi-step execution nodes (for post-actions)
from app.graphs.nodes.dispatcher_node import dispatcher_node
from app.graphs.nodes.aggregate_node import aggregate_node

# New workflow nodes (main tasks)
from app.graphs.nodes.work_request_node import work_request_node
from app.graphs.nodes.project_summary_node import project_summary_node
from app.graphs.nodes.project_metadata_node import project_metadata_node
from app.graphs.nodes.rag_workflow_node import rag_qa_node
from app.graphs.nodes.app_info_node import app_info_node


# Utility / fallback / post-actions
from app.graphs.nodes.help_node import help_node
from app.graphs.nodes.action_executor_node import action_executor_node
from app.graphs.nodes.fallback_node import fallback_node
from app.graphs.nodes.humanize_node import humanize_node


class HorizonState(TypedDict, total=False):
    # Core
    user_input: str
    intent: str
    domain: Optional[str]

    # Planning + execution
    plan: Dict[str, Any]
    task_results: List[Dict[str, Any]]

    # SQL path
    sql: Optional[str]
    sql_reasoning: Optional[str]
    rows: Optional[List[Dict[str, Any]]]
    row_count: Optional[int]
    rows_data: Optional[List[Dict[str, Any]]]

    # Actions / post flags (set by intent_node and/or planner)
    export: bool
    export_path: Optional[str]
    email: bool
    email_to: Optional[str]
    post_actions: Optional[List[Dict[str, Any]]]
    requires_multistep: Optional[bool]

    # LLM responses / aggregates
    response: Optional[str]
    aggregate_summary: Optional[Dict[str, Any]]
    human_summary_json: Optional[Dict[str, Any]]

    work_request_payload: Optional[Dict[str, Any]] = None
    project_summary_data: Optional[Dict[str, Any]] = None


# =============== ROUTING FUNCTIONS ===============


def _route_intent(state: HorizonState) -> str:
    """
    First step: route ONLY by main intent.
    Post-actions are handled AFTER the main task finishes.
    """
    intent = (state.get("intent") or "unknown").lower()

    # Conversational / irrelevant treated as help
    if intent in {"help", "irrelevant", "unknown"}:
        return "irrelevant"

    if intent in {
        "text_to_sql",
        "rag_query",
        "project_summary",
        "project_metadata",
        "work_request_generation",
        "app_info",
    }:
        state["main_task"] = intent
        return intent

    # Default fallback
    return "unknown"


def _after_main_task(state: HorizonState) -> str:
    """
    After ANY main task finishes, decide:
      - If post-actions exist → planner
      - Else → done (go to humanize)
    """
    # Prefer explicit post_actions from intent_node or planner
    post_actions = state.get("post_actions") or []

    has_post_actions = (
        bool(post_actions)
        or bool(state.get("requires_multistep"))
        or bool(state.get("email"))
        or bool(state.get("export"))
    )

    if has_post_actions:
        return "planner"

    return "done"


def _next_after_dispatch(state: HorizonState) -> str:
    plan = state.get("plan", {}) or {}
    subs = plan.get("subtasks", []) or []
    done = len(state.get("task_results", []) or [])
    if done < len(subs):
        return "dispatcher"
    return "aggregate"


def _next_after_aggregate(state: HorizonState) -> str:
    """
    After planner-driven subtasks, see if there are still post_actions
    that need execution by action_executor.
    """
    plan = state.get("plan", {}) or {}
    post_actions = plan.get("post_actions", []) or []

    if post_actions:
        return "action_executor"

    return "done"


# =============== BUILD GRAPH ===============


def build_horizon_brain_graph():

    g = StateGraph(HorizonState)
    g.add_node("route_intent", intent_node)

    g.add_node("work_request_generation", work_request_node)

    # Main task nodes
    g.add_node("sqlgen", sqlgen_node)
    g.add_node("sqlexec", sqlexec_node)

    g.add_node("project_summary", project_summary_node)
    g.add_node("project_metadata", project_metadata_node)
    g.add_node("rag_qa", rag_qa_node)
    g.add_node("app_info", app_info_node)

    # Multi-step execution (for post-actions)
    g.add_node("planner", planner_node)
    g.add_node("dispatcher", dispatcher_node)
    g.add_node("aggregate", aggregate_node)
    g.add_node("action_executor", action_executor_node)

    # Utility / fallback
    g.add_node("irrelevant", help_node)
    g.add_node("unknown", fallback_node)
    g.add_node("humanize", humanize_node)

    # -------------------------
    # INTENT ROUTING (MAIN TASK ONLY)
    # -------------------------
    g.add_conditional_edges(
        "route_intent",
        _route_intent,
        {
            "work_request_generation": "work_request_generation",
            "text_to_sql": "sqlgen",  # SQL main task
            "rag_query": "app_info",  # RAG main task // from rq_qa to rag_query
            "app_info": "app_info",  # App info main task
            "project_summary": "project_summary",
            "project_metadata": "project_metadata",
            "app_info": "app_info",
            "irrelevant": "irrelevant",
            "unknown": "unknown",
        },
    )

    # -------------------------
    # SQL MAIN TASK: sqlgen → sqlexec → post-action check
    # -------------------------
    g.add_edge("sqlgen", "sqlexec")
    g.add_edge("sqlexec", END)
    # g.add_conditional_edges("sqlexec", _after_main_task, {
    #     "planner": "planner",
    #     "done": "humanize",
    # })

    # -------------------------
    # OTHER MAIN TASKS → post-action check
    # -------------------------
    g.add_conditional_edges(
        "rag_qa",
        _after_main_task,
        {
            "planner": "planner",
            "done": "humanize",
        },
    )

    g.add_conditional_edges(
        "app_info",
        _after_main_task,
        {
            "planner": "planner",
            "done": "humanize",
        },
    )

    g.add_conditional_edges(
        "project_metadata",
        _after_main_task,
        {
            "planner": "planner",
            "done": "humanize",
        },
    )

    g.add_edge("work_request_generation", END)
    g.add_edge("project_summary", END)
    # g.add_conditional_edges("work_request_generation", _after_main_task, {
    #     "done": "humanize",
    # })

    # -------------------------
    # PLANNER → DISPATCHER → AGGREGATE
    # (Only used when post-actions / multi-step are needed)
    # -------------------------
    g.add_edge("planner", "dispatcher")
    g.add_edge("dispatcher", "humanize")

    # g.add_conditional_edges("dispatcher", _next_after_dispatch, {
    #     "dispatcher": "dispatcher",
    #     "aggregate": "aggregate",
    # })

    g.add_conditional_edges(
        "aggregate",
        _next_after_aggregate,
        {
            "action_executor": "action_executor",
            "done": "humanize",
        },
    )

    # -------------------------
    # ACTION EXECUTION → FINAL
    # -------------------------
    g.add_edge("action_executor", "humanize")

    # -------------------------
    # ENDINGS
    # -------------------------
    g.add_edge("irrelevant", END)
    g.add_edge("unknown", END)
    g.add_edge("humanize", END)

    g.set_entry_point("route_intent")
    return g.compile()
