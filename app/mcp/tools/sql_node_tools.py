schema_tool = [
    {
        "type": "function",
        "function": {
            "name": "getSchema",
            "description": "Return schema modules to help generate SQL. Always call this before writing SQL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "modules": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "projects_module",
                                "vendors_module",
                                "project_labours_module",
                                "scope_and_approvals_module",
                            ],
                        },
                        "description": "Schema modules to load.",
                        "minItems": 1,
                    }
                },
                "required": ["modules"],
                "additionalProperties": False,
            },
        },
    }
]


tools = [
    {
        "type": "function",
        "function": {
            "name": "executeSQL",
            "description": "Execute a read-only SELECT SQL query against the reporting database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL SELECT query to execute. Must NOT modify data.",
                    }
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "projectData",
            "description": "Fetch project records via the Laravel API with optional filters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filters": {
                        "type": "object",
                        "description": "Optional filters: project_id, client_id, business_unit_id, country_id, status_code, is_active etc.",
                        "additionalProperties": True,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of projects to return.",
                        "minimum": 1,
                        "maximum": 500,
                    },
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
]
