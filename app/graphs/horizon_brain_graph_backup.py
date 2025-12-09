# app/graphs/horizon_brain_graph.py

from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END

# Core LLM nodes
from app.graphs.nodes.intent_node import intent_node
from app.graphs.nodes.planner_node import planner_node

# Execution nodes
from app.graphs.nodes.sqlgen_node import sqlgen_node
from app.graphs.nodes.sqlexec_node import sqlexec_node
from app.graphs.nodes.dispatcher_node import dispatcher_node
from app.graphs.nodes.aggregate_node import aggregate_node
from app.graphs.nodes.export_node import export_node
from app.graphs.nodes.email_node import email_node

# Utility / fallback nodes
from app.graphs.nodes.help_node import help_node
from app.graphs.nodes.greeting_node import greeting_node
from app.graphs.nodes.fallback_node import fallback_node
from app.graphs.nodes.humanize_node import humanize_node

class HorizonState1(TypedDict, total=False):
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

    # Actions / post flags
    export: bool
    export_path: Optional[str]
    email: bool
    email_to: Optional[str]
    response: Optional[str]
    aggregate_summary: Optional[Dict[str, Any]]
    human_summary_json: Optional[Dict[str, Any]]


# =============== ROUTING FUNCTIONS ===============

def _route_intent(state: HorizonState) -> str:
    """
    Decides where to go next after the intent_node.
    """
    intent = (state.get("intent") or "unknown").lower()

    # Simple conversational flows
    if intent in {"help", "greeting", "smalltalk"}:
        return intent

    # Unknown → fallback
    if intent == "unknown":
        return "unknown"

    # SQL queries may be simple or compound (export/email/etc.)
    if intent == "sql_query":
        export = state.get("export")
        email = state.get("email")
        # If user mentioned export/email, treat as complex
        if export or email:
            return "planner"
        return "sqlgen"  # simple SQL path

    # Analytics, rag_query, or action → complex plan required
    if intent in {"analytics", "rag_query", "action"}:
        return "planner"

    # Default fallback
    return "unknown"


def _next_after_sqlexec(state: HorizonState) -> str:
    if state.get("export"):
        return "export"
    if state.get("email"):
        return "send_email"
    return "done"


def _next_after_dispatch(state: HorizonState) -> str:
    plan = state.get("plan", {}) or {}
    subs = plan.get("subtasks", []) or []
    done = len(state.get("task_results", []) or [])
    if done < len(subs):
        return "dispatcher"
    return "aggregate"


def _next_after_aggregate(state: HorizonState) -> str:
    plan = state.get("plan", {}) or {}
    if plan.get("follow_up"):
        return "planner"
    if state.get("export") or state.get("email"):
        return "export"
    return "done"


# =============== GRAPH BUILD ===============

def build_horizon_brain_graph():
    g = StateGraph(HorizonState)

    # Entry: LLM intent classifier
    g.add_node("route_intent", intent_node)

    # Simple SQL pipeline
    g.add_node("sqlgen", sqlgen_node)
    g.add_node("sqlexec", sqlexec_node)

    # Complex / multi-step flow
    g.add_node("planner", planner_node)
    g.add_node("dispatcher", dispatcher_node)
    g.add_node("aggregate", aggregate_node)

    # Post actions
    g.add_node("export_file", export_node)
    g.add_node("send_email", email_node)

    # Conversational
    g.add_node("help", help_node)
    g.add_node("greeting", greeting_node)
    g.add_node("unknown", fallback_node)
    g.add_node("humanize", humanize_node)
    # =============== CONDITIONAL ROUTING ===============

    # From intent classification
    g.add_conditional_edges("route_intent", _route_intent, {
        "sqlgen": "sqlgen",          # simple SQL
        "planner": "planner",        # complex plan required
        "help": "help",
        "greeting": "greeting",
        "smalltalk": "greeting",
        "unknown": "unknown",
    })

    # Simple SQL chain
    g.add_edge("sqlgen", "sqlexec")
    g.add_conditional_edges("sqlexec", _next_after_sqlexec, {
        "export": "export_file",
        "send_email": "send_email",
        "done": "humanize",  
    })

    # Complex planning chain
    g.add_edge("planner", "dispatcher")
    g.add_conditional_edges("dispatcher", _next_after_dispatch, {
        "dispatcher": "dispatcher",
        "aggregate": "aggregate",
    })
    g.add_conditional_edges("aggregate", _next_after_aggregate, {
        "planner": "planner",
        "export": "export_file",
        "done": "humanize",  # previously END
    })

    # Post actions
    g.add_edge("export_file", "send_email")
    g.add_edge("send_email", "humanize")

    # Conversational ends
    g.add_edge("help", END)
    g.add_edge("greeting", END)
    g.add_edge("unknown", END)
    g.add_edge("humanize", END)

    g.set_entry_point("route_intent")
    return g.compile()
