# app/graphs/nodes/planner_node.py

import json
import logging
from app.models.llm.factory import get_llm

log = logging.getLogger("graph>node>planner")
PLANNER_PROMPT = """
You are a SENIOR AI TASK PLANNER for an enterprise assistant.

IMPORTANT CONTEXT:
- The MAIN TASK for this request has ALREADY been executed (e.g. SQL query, RAG answer, summary, work request).
- Your job NOW is ONLY to plan FOLLOW-UP subtasks and POST-ACTIONS.
- DO NOT repeat the main task.
- DO NOT generate new sql_query, rag_query, project_summary, metadata_query, or work_request subtasks
  unless the user VERY CLEARLY asks for an additional, separate one.

Your responsibilities in THIS PHASE:
1. Decide if ANY extra subtasks are needed AFTER the main result.
2. Decide which POST-ACTIONS to perform (email, export, download, notify, etc.).
3. Keep everything as SIMPLE and MINIMAL as possible.

SUBTASK TYPES allowed in this phase:
- "action"   → extra side-effects that are NOT simple email/export/download
               e.g.: "notify_user", "webhook_call", "create_ticket", etc.
- "explain"  → only if the user explicitly asks for an explanation AFTER the result
               e.g.: "then explain this to a junior", "then break it down in simple terms"

You MUST NOT use in this phase:
- "sql_query"
- "rag_query"
- "metadata_query"
- "project_summary"
- "work_request"

POST-ACTIONS (what to do with the ALREADY-COMPUTED result):
- "email"
- "download"
- "export"
- "notify"
- "create"
- "save"
- "webhook"
(and more if clearly needed)

JSON SCHEMA (STRICT):

{
  "plan_summary": "one-line summary of follow-up steps",
  "subtasks": [
    {
      "id": "s1",
      "type": "action | explain",
      "action": "export_file | email_report | notify_user | webhook | ...",
      "question": "If type=explain, the question to answer",
      "params": {},
      "requires": []
    }
  ],
  "post_actions": [
    {
      "type": "email | export | download | notify | create | save | webhook",
      "params": {}
    }
  ]
}

CRITICAL RULES:

- If the user ONLY says things like:
    "and then email it",
    "and email to X",
    "and send me the result",
    "and export/download it"
  → DO NOT create any subtasks.
  → Leave "subtasks": [].
  → Put everything into "post_actions" only.

- Only create a subtask when there is an additional behavior BEYOND email/export:
    e.g. "then explain it to a junior engineer"
         → create an "explain" subtask.
    e.g. "then send a Slack notification to #ops"
         → you may use a single 'notify' post_action, or an 'action' subtask if complex logic is required.

- Use the MINIMAL number of subtasks.
- Prefer using ONLY post_actions when possible.

EXAMPLES (VERY IMPORTANT):

1) User: "list 10 projects and then email to john@acme.com"
   → The SQL/listing is already done.
   → Desired plan:
   {
     "plan_summary": "Email the 10 listed projects to john@acme.com.",
     "subtasks": [],
     "post_actions": [
       {
         "type": "email",
         "params": { "to": "john@acme.com" }
       }
     ]
   }

2) User: "summarize project Titan and then explain it to a junior engineer and email it"
   → Main summary already done.
   → You may add:
   {
     "plan_summary": "Explain the summary in simple terms and email it.",
     "subtasks": [
       {
         "id": "s1",
         "type": "explain",
         "question": "Explain the existing project summary in simple terms for a junior engineer.",
         "action": null,
         "params": {},
         "requires": []
       }
     ],
     "post_actions": [
       {
         "type": "email",
         "params": { "to": "someone@example.com" }
       }
     ]
   }

3) User: "show revenue per BU for this year and then export it to Excel"
   → The analytics are already done.
   → Desired plan:
   {
     "plan_summary": "Export the revenue-by-BU result to Excel.",
     "subtasks": [],
     "post_actions": [
       {
         "type": "export",
         "params": { "format": "excel" }
       }
     ]
   }

STRICT JSON ONLY. No comments, no explanations.
"""

async def planner_node(state):
    log.info("-------------LANDED IN PLANNER NODE-------------")
    llm = get_llm()

    user_input = state.get("user_input", "")
    main_task = state.get("main_task")  # Injected earlier in route_intent or task nodes

    # NEW: Tell planner which main task already ran
    system_content = PLANNER_PROMPT + f"\n\nMAIN_TASK_ALREADY_DONE: {main_task}\n"

    try:
        resp = await llm.chat([
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_input}
        ])

        text = resp.choices[0].message.content
        log.info(f"Raw planner output: {text}")
        plan = json.loads(text)

    except Exception as e:
        log.exception("Planner failed: %s", e)
        plan = {
            "plan_summary": "Planner failed.",
            "subtasks": [],
            "post_actions": []
        }

    state["plan"] = plan
    return state
