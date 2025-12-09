# app/graphs/nodes/export_node.py
from app.services.export_service import ExportService

def export_node(state: dict) -> dict:
    rows = state.get("rows") or []
    svc = ExportService()
    # Unique filename per export (optional)
    from datetime import datetime
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"horizon_export_{stamp}.xlsx"

    export_path = svc.save_to_temp_excel(rows, filename=filename)
    return {**state, "export_path": export_path}
