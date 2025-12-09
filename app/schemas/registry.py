SCHEMA_REGISTRY = {
    "tables": {
        "projects": {
            "description": "Master table of projects at each site. One row per project.",
            "columns": {
                "id": {
                    "type": "INT", "pk": True, "nullable": False,
                    "description": "Unique project identifier."
                },
                "site_name": {
                    "type": "VARCHAR(255)", "nullable": False,
                    "description": "Human-readable site or facility name tied to the project location."
                },
                "project_title": {
                    "type": "VARCHAR(255)", "nullable": False,
                    "description": "Short descriptive title of the project."
                },
                "project_status_code": {
                    "type": "VARCHAR(50)", "nullable": False,
                    "description": "Current lifecycle status CODE for the project (FK to project_statuses.status_code). "
                                   "This stores a code (e.g., 1,2,34,25 etc), not the human-readable name."
                },
                "cost": {
                    "type": "DECIMAL(18,2)", "nullable": True,
                    "description": "Total internal cost of the project in base currency.", "units": "currency"
                },
                "total_margin_value": {
                    "type": "DECIMAL(18,2)", "nullable": True,
                    "description": "Absolute margin value (revenue - cost).", "units": "currency",
                    "aggregation_hint": "SUM"
                },
                "total_quote_value": {
                    "type": "DECIMAL(18,2)", "nullable": True,
                    "description": "Quoted price offered to client (potential revenue).", "units": "currency",
                    "aggregation_hint": "SUM"
                },
            },
            "indexes_hint": ["id", "project_status_code"]
        },

        "project_statuses": {
            "description": "Lookup/dimension table of valid project statuses: a machine code and a human-readable name.",
            "columns": {
                "status_code": {
                    "type": "VARCHAR(50)", "pk": True, "nullable": False,
                    "description": "Canonical STATUS CODE (e.g., 1,12,25 etc). "
                                   "Referenced by projects.project_status_code."
                },
                "name": {
                    "type": "VARCHAR(100)", "nullable": False,
                    "description": "Human-readable STATUS NAME (e.g., 'Billing Completed', 'Work Order Closed', 'Lost').",
                    "uniqueness_hint": "Values are unique per code; case-insensitive comparisons are allowed."
                },
                "id": {
                    "type": "INT", "nullable": True,
                    "description": "Optional surrogate key (not used in joins)."
                }
            },
            "indexes_hint": ["status_code", "name"]
        },
    },

    "relations": [
        {"from": "projects.project_status_code", "to": "project_statuses.status_code", "type": "MANY_TO_ONE"}
    ],

    "notes": [
        # Guardrails
        "Only SELECT statements are allowed. Read-only queries.",
        "Never use SELECT *; always name columns explicitly.",
        "Use MySQL syntax only. The SQL must be execution-ready.",
        "Use LIMIT <= {MAX_LIMIT}.",

        # Critical rule for status filtering:
        "When the user mentions a HUMAN-READABLE STATUS (e.g., 'Billing Completed'), you MUST JOIN project_statuses "
        "and filter on project_statuses.name (case-insensitive). Do NOT compare human names directly to projects.project_status_code.",

        # Join guidance
        "Join projects.project_status_code = project_statuses.status_code when you need status details or when the user provides status by name."
    ],
}
