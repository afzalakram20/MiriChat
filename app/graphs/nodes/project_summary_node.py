# project_summarization_node.py

from app.llms.runnable.llm_provider import get_chain_llm
from app.core.config import settings
import re
import json
import logging
from typing import Dict, Any, List, Optional
from app.controllers.tool_impl import getProjectData
import httpx
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser

log = logging.getLogger("project_summarization_node")

# -----------------------------
# CONFIG
# -----------------------------
PROJECT_SERVICE_URL = (
    "http://127.0.0.1:7890/horizon-extra-works/mcp/api/v1/projects_by_ref_ids"
)


class ProjectSummaryModel(BaseModel):
    reasoning: str = Field(
        ...,
        description=(
            "Brief chain-of-thought style internal reasoning explaining how you "
            "derived the summary. Keep it short and high-level."
        ),
    )
    overview: str = Field(
        ...,
        description="High-level overview of the project in clear, concise business English.",
    )
    project_scope: str = Field(
        ...,
        description=(
            "Summarized scope of works, combining notes/problem/scope/justification/"
            "non_approval_effect into a clean, short narrative."
        ),
    )
    status_history: str = Field(
        ...,
        description="Summarized status history and key milestones in chronological order.",
    )
    project_financials: str = Field(
        ...,
        description=(
            "Clear summary of quote values, margins, and financial summary "
            "in business language; keep numeric values accurate."
        ),
    )
    epic_form: str = Field(
        ...,
        description="Summary of EPIC form or explicitly 'N/A' if no useful data.",
    )
    pors: str = Field(
        ...,
        description="Summary of Purchase Order Requests or 'N/A' if there is none.",
    )
    close_out: str = Field(
        ...,
        description=(
            "Summary of closeout and billing / client closeout information, or 'N/A'."
        ),
    )
    blockers: List[str] = Field(
        ...,
        description=(
            "List of blockers (missing items / issues preventing project completion). "
            "If none, return ['N/A']."
        ),
    )
    next_steps: List[str] = Field(
        ...,
        description=(
            "List of actionable next steps to move the project forward. "
            "If none, return ['N/A']."
        ),
    )


SYSTEM_MESSAGE = """ 




"""


# -----------------------------
# Pydantic Models
# -----------------------------
class SearchParamModel(BaseModel):
    """LLM #1 — Extract search parameter"""

    ref_id: Optional[str] = None
    project_title: Optional[str] = None


# class ProjectSummaryModel(BaseModel):
#     """LLM #2 — Summarization output"""
#     reasoning: str
#     overview: str
#     project_scope: str
#     status_history: str
#     project_financials: str
#     epic_form: str
#     pors: str
#     close_out: str
#     blockers: List[str]
#     next_steps: List[str]


# -----------------------------
# Helper — Call Laravel API
# -----------------------------
async def _fetch_project_from_laravel(
    ref_id: Optional[str], project_title: Optional[str]
):
    payload = {"ref_id": ref_id or "", "project_title": project_title or ""}

    log.info(f"Laravel API Request Payload: {payload}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(PROJECT_SERVICE_URL, json=payload)

    if resp.status_code != 200:
        raise RuntimeError(f"Laravel API failed: {resp.status_code} → {resp.text}")

    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"Laravel API success=false → {data}")

    projects = data.get("projects", [])
    if not projects:
        raise ValueError("No project returned from Laravel API.")

    return projects[0]  # we take the first match


# -----------------------------
# MAIN NODE
# -----------------------------
async def project_summary_node(state: Dict[str, Any]) -> Dict[str, Any]:

    log.info("******* Entered project_summarization_node ********")

    # ----------------------------------------------------
    # STEP 1 — Extract search parameter using LLM
    # ----------------------------------------------------
    user_query = state.get("user_input", "").strip()
    if not user_query:
        raise ValueError("Missing user_input for summarization.")

    log.info(f"User Query for Search Param Extraction: {user_query}")
    extractor_llm = get_chain_llm()
    # extractor_llm = ChatOpenAI(
    #     model="gpt-4o-mini", temperature=0.3, openai_api_key=settings.OPENAI_API_KEY
    # )

    extractor_parser = PydanticOutputParser(pydantic_object=SearchParamModel)
    extractor_format = extractor_parser.get_format_instructions()

    extractor_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a system that extracts search parameters for project summarization.\n"
                "You will receive recent chat history (assistant and user turns). Use it to resolve follow‑ups, e.g., "
                "if the user says 'same project' or 'update previous answer', infer the last referenced project (ref_id or title) from history.\n"
                "User can either give a CBRE project reference ID like 'US-EW-06112025-12987' "
                "OR a project_title like 'Chiller Pump Upgrade'.\n\n"
                "Rules:\n"
                "- If ref_id pattern detected (AA-EW-ddMMyyyy-xxxxx) → fill ref_id.\n"
                "- Otherwise → treat the input as project_title.\n"
                "- If neither is explicitly provided but recent history mentions a project id/title, reuse that as the target.\n"
                "- Return ONLY the JSON.\n",
            ),
            MessagesPlaceholder("chat_history"),
            ("human", "User query:\n{query}\n\n" "Return JSON:\n{format}"),
        ]
    )

    extractor_chain = extractor_prompt | extractor_llm | extractor_parser

    search_param_obj: SearchParamModel = extractor_chain.invoke(
        {"query": user_query, "format": extractor_format, "chat_history": state.get("chat_history") or []}
    )

    ref_id = search_param_obj.ref_id
    project_title = search_param_obj.project_title

    log.info(
        f"Extracted Search Params → ref_id={ref_id}, project_title={project_title}"
    )

    # ----------------------------------------------------
    # STEP 2 — Call Laravel API with extracted params
    # ----------------------------------------------------
    project_data = await getProjectData([ref_id])

    log.info(f"Project Data Successfully Retrieved From Laravel {project_data}")
    project_data = project_data["projects"][0]
    state["project_raw_data"] = project_data  # optional, helpful for debugging
    log.info(f"Single Project Data Successfully Retrieved From Laravel {project_data}")
    # project_json_str = json.dumps(project_data, ensure_ascii=False, indent=2)

    # ----------------------------------------------------
    # STEP 3 — Summarize using LLM
    # ----------------------------------------------------
    summarizer_llm = get_chain_llm()
    # summarizer_parser = PydanticOutputParser(pydantic_object=ProjectSummaryModel)
    # summarizer_format = summarizer_parser.get_format_instructions()

    summarizer_parser = PydanticOutputParser(pydantic_object=ProjectSummaryModel)
    summarizer_format_instructions = summarizer_parser.get_format_instructions()

    project_json_str = json.dumps(project_data, ensure_ascii=False, indent=2)

    summarizer_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are an expert CBRE project summarization assistant.\n"
                    "You receive raw project data from backend APIs and must generate "
                    "a clean, concise, business-professional JSON summary.\n\n"
                    "You MUST follow these rules:\n"
                    "0. Conversation history: You will receive recent chat history. Use it to maintain continuity. "
                    "   If the user asks to adjust the previous summary (e.g., 'revise overview', 'add blockers', "
                    "   'shorter bullets'), update ONLY the requested parts and preserve prior decisions (tone, target project) "
                    "   unless the user clearly changes them.\n"
                    "   - If ambiguity remains, prefer the previously referenced project/ref_id from history.\n"
                    "   - Carry over specific constraints from earlier turns (e.g., short bullets, executive tone) unless overridden.\n"
                    "1. Rewrite scope fields (notes, problem, scope, justification, "
                    "   non_approval_effect) into short, summarized, clean human language.\n"
                    "2. When you have no data for an output field, set its value to 'N/A'.\n"
                    "3. Never copy text word-for-word unless required (e.g., financial values, "
                    "   reference numbers). Paraphrase and clean language.\n"
                    "4. Summaries must be factual, fluent, and business-professional.\n"
                    "5. Follow the exact output structure:\n"
                    "      - reasoning\n"
                    "      - overview\n"
                    "      - project_scope\n"
                    "      - status_history\n"
                    "      - project_financials\n"
                    "      - epic_form\n"
                    "      - pors\n"
                    "      - close_out\n"
                    "      - blockers[]\n"
                    "      - next_steps[]\n"
                    "6. Blockers are the missing things in project completion (issues / gaps).\n"
                    "7. Next steps are the implementation actions to resolve blockers and "
                    "   move the project forward.\n\n"
                    "If a particular section (e.g. EPIC form, POs, close out) genuinely has "
                    "no information in the input, you MUST explicitly set that section to 'N/A'.\n\n"
                    "You MUST respond ONLY with JSON that matches the format instructions."
                ),
            ),
            MessagesPlaceholder("chat_history"),
            (
                "human",
                (
                    "Here is the raw project data returned from the backend Laravel API:\n\n"
                    "{project_json}\n\n"
                    "Use this data to generate a structured project summary.\n\n"
                    "Follow these format instructions exactly:\n"
                    "{format_instructions}"
                ),
            ),
        ]
    )

    summarizer_chain = summarizer_prompt | summarizer_llm | summarizer_parser

    # chain_input = {
    #     "project_json": project_json_str,
    #     "format_instructions": summarizer_format,
    # }

    summary_obj: ProjectSummaryModel = summarizer_chain.invoke(
        {
            "project_json": project_json_str,
            "format_instructions": summarizer_format_instructions,
            "chat_history": state.get("chat_history") or [],
        }
    )

    summary_data = summary_obj.dict()

    log.info("Project Summarization Completed Successfully")

    # ----------------------------------------------------
    # STEP 4 — Attach summary to state
    # ----------------------------------------------------
    state["project_summary_data"] = summary_data

    log.info(f"Project project_summary_data before exit node{state}")

    return state
