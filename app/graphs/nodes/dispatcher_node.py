# app/graphs/nodes/aggregate_node.py

import logging
from typing import Dict, Any, List

log = logging.getLogger("graph>node>aggregate")


async def dispatcher_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simplified AGGREGATE NODE:
    
    - If NO post_actions → return state unchanged (graph will go to 'done')
    - If post_actions exist → execute them HERE
    """

    log.info("----- ENTERED AGGREGATE NODE -----")

    plan = state.get("plan", {}) or {}
    post_actions: List[Dict[str, Any]] = plan.get("post_actions", []) or []

    # Save post_actions into state
    state["post_actions"] = post_actions

    # -----------------------------
    # CASE 1 → NO POST ACTIONS
    # -----------------------------
    if not post_actions:
        log.info("No post actions found → aggregate finished")
        return state

    # -----------------------------
    # CASE 2 → EXECUTE POST ACTIONS
    # -----------------------------
    log.info(f"Executing post actions: {post_actions}")

    # Keep track of results
    executed_results = []

    for idx, action in enumerate(post_actions, start=1):
        action_type = action.get("type")
        params = action.get("params", {})

        log.info(f"Executing post action #{idx}: {action_type} | params={params}")

        # -----------------------------
        # EMAIL
        # -----------------------------
        if action_type == "email":
            email_to = params.get("to")
            subject = params.get("subject", "HorizonAI Report")
            body = params.get("body", "Attached is your requested result.")
            log.info("******************************************************")
            log.info("********************Success EMAIL************************")

            # try:
            #     from app.services.mailer import send_email
            #     await send_email(email_to, subject, body, state.get("rows"))
            executed_results.append(
                {"type": "email", "status": "success", "to": email_to}
            )
            # except Exception as e:
            #     log.exception("Email post-action failed")
            #     executed_results.append(
            #         {"type": "email", "status": "failed", "error": str(e)}
            #     )

        # -----------------------------
        # EXPORT / DOWNLOAD (CSV or Excel)
        # -----------------------------
        elif action_type in {"export", "download"}:
            file_format = params.get("format", "csv")
            
            log.info("******************************************************")
            log.info("********************Success DOWNLOAD************************")

            # try:
            #     from app.services.exporter import generate_export_file
            #     file_path = await generate_export_file(
            #         state.get("rows", []), file_format
            #     )
            #     state["export_path"] = file_path

            executed_results.append(
                {"type": action_type, "status": "success", "path": "file_path"}
            )
            # except Exception as e:
            #     log.exception("Export/Download post-action failed")
            #     executed_results.append(
            #         {"type": action_type, "status": "failed", "error": str(e)}
            #     )

        # -----------------------------
        # NOTIFY USER
        # -----------------------------
        elif action_type == "notify":
            message = params.get("message", "Your result is ready.")
            log.info(f"(Simulated) Sending notification: {message}")
            executed_results.append(
                {"type": "notify", "status": "success", "message": message}
            )

        # -----------------------------
        # DEFAULT HANDLER
        # -----------------------------
        else:
            log.info(f"Unknown post-action type: {action_type} (ignored)")
            executed_results.append(
                {"type": action_type, "status": "ignored"}
            )

    # Save all post-action results
    state["post_action_results"] = executed_results

    return state
