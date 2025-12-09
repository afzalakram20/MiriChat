from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END
from app.graphs.nodes.intent_node import intent_node
from app.graphs.nodes.sqlgen_node import sqlgen_node
from app.graphs.nodes.sqlexec_node import sqlexec_node
from app.graphs.nodes.export_node import export_node
from app.graphs.nodes.email_node import email_node
from app.graphs.nodes.help_node import help_node
from app.graphs.nodes.greeting_node import greeting_node
from app.graphs.nodes.fallback_node import fallback_node
from app.graphs.nodes.intent_sql_ext import parse_sql_intent


class HorizonState(TypedDict, total=False):
    user_input: str
    intent: str
    export: bool
    email: bool
    email_to: Optional[str]
    sql: Optional[str]
    rows: Optional[List[Dict[str, Any]]]
    row_count: Optional[int]
    export_path: Optional[str]
    email_sent: Optional[bool]
    response: Optional[str]

def _next_after_sqlexec(state: dict) -> str:
    # Decide what to do after SQL execution
    if state.get("email"):
        # If email is requested, ensure we export first to get a file
        if state.get("export"):
            return "export"
        else:
            return "export"  # force export before email
    if state.get("export"):
        return "export"
    return "done"

def _route_intent(state: dict) -> str:
    # Must return one of the keys used in edges below
    return state.get("intent", "unknown")

def build_horizon_txt_to_sql_graph():
    # Provide explicit state schema per langgraph>=0.2
    g = StateGraph(HorizonState)

    # Universal entry
    g.add_node("route_intent", intent_node)

    # SQL pipeline (modular)
    g.add_node("parse_sql_intent", parse_sql_intent)
    g.add_node("sqlgen", sqlgen_node)
    g.add_node("sqlexec", sqlexec_node)
    g.add_node("export_file", export_node)
    g.add_node("send_email", email_node)

    # Non-SQL branches
    g.add_node("help", help_node)
    g.add_node("greeting", greeting_node)
    g.add_node("unknown", fallback_node)

    # Route by intent
    g.add_conditional_edges("route_intent", _route_intent, {
        "sql_query": "parse_sql_intent",
        "help": "help",
        "greeting": "greeting",
        "analytics": "unknown",   # placeholder; add analytics node later
        "unknown": "unknown",
    })

    # SQL flow
    g.add_edge("parse_sql_intent", "sqlgen")
    g.add_edge("sqlgen", "sqlexec")
    g.add_conditional_edges("sqlexec", _next_after_sqlexec, {
        "export": "export_file",
        "done": END,  # finish after rows are in state
    })
    # Export then optionally email
    g.add_edge("export_file", "send_email")

    # Terminal edges for non-SQL branches and email completion
    g.add_edge("help", END)
    g.add_edge("greeting", END)
    g.add_edge("unknown", END)
    g.add_edge("send_email", END)

    # Entry point and compile
    g.set_entry_point("route_intent")
    return g.compile()
