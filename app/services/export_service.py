"""Provides both file-save (for email) and streaming (for HTTP download) helpers."""

from pathlib import Path
import io
import logging
from typing import List, Dict, Any

import pandas as pd
from fastapi.responses import StreamingResponse

log = logging.getLogger("app.services.export")


class ExportService:
    def save_to_temp_excel(self, rows: List[Dict[str, Any]], filename: str = "horizon_export.xlsx") -> str:
        """Save rows to an Excel file under <repo_root>/exports and return the path."""
        try:
            root_dir = Path(__file__).resolve().parent.parent.parent
            export_dir = root_dir / "exports"
            export_dir.mkdir(exist_ok=True)

            file_path = export_dir / filename
            pd.DataFrame(rows or []).to_excel(file_path, index=False)
            log.info("export file written: %s", file_path)
            return str(file_path)
        except Exception as e:
            log.exception("Failed to save export file: %s", e)
            return ""

    def to_streaming_excel(self, rows: List[Dict[str, Any]], filename: str = "export.xlsx") -> StreamingResponse:
        df = pd.DataFrame(rows or [])
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Data", index=False)
        buf.seek(0)
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers,
        )
