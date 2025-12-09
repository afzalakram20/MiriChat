from typing import Dict, Any

def perform_action(task: Dict[str, Any]) -> Dict[str, Any]:
    action = (task.get("action") or "").lower()
    params = task.get("params", {}) or {}
    if action == "email_report":
        # Actual email sending happens in the graph's export->email nodes.
        return {"status": "queued_email", "to": params.get("to") or params.get("email_to")}
    return {"status": "noop", "action": action}
