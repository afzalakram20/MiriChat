# app/graphs/nodes/email_node.py
from typing import Dict, Any
import logging
from app.services.email_service import EmailService

log = logging.getLogger("app.graphs.nodes.email")

def email_node(state: Dict[str, Any]) -> Dict[str, Any]:
    log.info("here at email node11111")
    log.info(f"here at email {state}")
    # Only send if explicitly requested and we have a recipient + file
    # if not state.get("email"):
    #     return {**state, "email_sent": False, "email_error": "Email flag not set."}

    email_to= state.get("email_to")
    export_path = state.get("export_path")  
    log.info(f"here at email export_path{export_path}")
    log.info(f"here at email email_to{email_to}")
    if not email_to:
        return {**state, "email_sent": False, "email_error": "Missing email_to."}
    if not export_path:
        return {**state, "email_sent": False, "email_error": "Missing export_path."}
    log.info("here at email node2222")
    svc = EmailService()
    subject = "Requested Report"
    body = "Please find the requested report attached."
    log.info("here at email 33333")
    ok = svc.send_with_attachment(email_to, subject, body, export_path)
    if not ok:
        return {**state, "email_sent": False, "email_error": "Send failed."}

    log.info("Emailed report to %s", email_to)
    return {**state, "email_sent": True}
