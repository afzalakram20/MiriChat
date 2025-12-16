from typing import Dict, Any
import logging
import json
import re

from app.services.render import render_json_fallback
from app.core.config import settings
from app.llms.runnable.llm_provider import get_chain_llm

log = logging.getLogger("graph>node>humanize")


async def humanize_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Final node: Summarizes outputs from all previous nodes and builds
    AI-readable JSON (human_summary_json). Uses same LLM calling style as generate_sql_from_question().
    """
    llm = get_chain_llm(state.get("model_key"), state.get("model_id"))
    rows = state.get("rows") or []
    agg = state.get("aggregate_summary") or {}
    plan = state.get("plan") or {}
    reasoning = state.get("sql_reasoning") or "N/A"

    # --- Prepare compact JSON snippets for plan and agg ---
    plan_json = json.dumps(plan, indent=2, ensure_ascii=False)
    agg_json = json.dumps(agg, indent=2, ensure_ascii=False)
    sample_json = json.dumps(rows, indent=2, ensure_ascii=False)
    messages = [
        {
            "role": "system",
            "content": """
    You are an expert business analyst who writes clear executive summaries for management.
    Your summaries should be easy to understand, professional, and free of technical or engineering language.

    STRICT RULES:
    - DO NOT mention: LangGraph, workflows, pipelines, algorithms, LLMs, nodes, tools, SQL, databases, schemas, or queries.
    - DO NOT describe *how* the system works internally.
    - ONLY focus on business meaning and insights.
    - Use clear executive language suitable for directors and senior managers.
    """
        },
        {
            "role": "user",
            "content": f"""
    Please summarize the analytical results in a manager-friendly way.

    Business Context:
    - Purpose & reasoning behind the results:
    {reasoning}

    - Overview of the plan:
    {plan_json}

    - Aggregate metrics or computed totals:
    {agg_json}

    - Example of retrieved data (sample rows):
    {sample_json}

    Instructions:
    1. Write a concise 3–5 sentence executive summary.
    2. Focus on WHAT the data represents — not how it was processed.
    3. Highlight key insights, patterns, trends, or implications.
    4. Use professional business language suitable for senior management.
    5. Do NOT mention technical details like SQL, databases, or system components.
    """
        }
    ]

    try:
        # === LLM Call (consistent with generate_sql_from_question) ===
        log.info(f"the human messages---{messages}")
        res = await llm.chat(messages)
        # Normalize output across providers
        if hasattr(res, "content"):
            text = res.content or ""
        elif isinstance(res, str):
            text = res
        elif hasattr(res, "choices"):  # legacy OpenAI-like response
            try:
                text = res.choices[0].message.content or ""
            except Exception:
                text = ""
        else:
            text = str(res or "")
        log.info(f"the human summary---{text}")
        # === Clean and normalize ===
        summary_text = re.sub(r"^```|```$", "", text.strip(), flags=re.M).strip()

        # === Build final structured summary ===
        state["human_summary_json"] = {
            **render_json_fallback(state),
            "summary_text": summary_text,
        }
        return state

    except Exception as e:
        log.exception("humanize_node failed: %s", e)
        # fallback (non-LLM)
        state["human_summary_json"] = {
            **render_json_fallback(state),
            "summary_text": "Summary generation failed. Returned fallback JSON rendering only.",
        }
        return state
