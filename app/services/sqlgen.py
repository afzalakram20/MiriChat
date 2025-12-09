import json, re
from app.schemas.registry import SCHEMA_REGISTRY
from app.core.config import settings
from app.models.llm.factory import get_llm
SQL_HEADER = """
You are an expert MySQL SQL writer and data-security specialist.
Your job is to generate ONE and ONLY ONE ready-to-execute MySQL SELECT statement.

You must follow all rules exactly and return ONLY the SQL code — no markdown, no explanation, no commentary.
The generated SQL must be syntactically valid and executable in MySQL as-is.
"""

SQL_RULES = f"""
Strict Rules:
- Absolutely ONLY readonly SELECT statements. Never use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, or any other data definition or modification commands.
- The query must be fully execution-ready (no placeholders, no explanations).
- Never use SELECT * or any wildcard selection. Always specify explicit column names.
- Only use columns that exist in the provided schema and never add new or unknown ones.
- The number of selected columns must not exceed those defined in the schema. Do not infer or imagine extra columns.
- The query must respect the maximum limit of {settings.MAX_LIMIT} rows. If the user requests more, cap it at this limit.
- Only use MySQL syntax and conventions.
- Allowed tables: projects, project_financials.
- Allowed join: projects.id = project_financials.project_id (when needed).
- Use proper WHERE filters and LIMIT clauses to ensure data safety and efficiency.
- When user refers to year or month, use YEAR(period_date) or MONTH(period_date) accordingly.
- No schema modification, DDL, or administrative statements under any circumstances.
- Return exactly ONE SQL statement, clean and ready to execute — no text, no comments, no explanations, no markdown.
"""


async def generate_sql_from_question(question: str) -> str:
    schema_json = json.dumps(SCHEMA_REGISTRY, indent=2)
    prompt = (
        SQL_HEADER + "\n" + SQL_RULES + "\n\n" +
        f"Schema:\n{schema_json}\n\n" +
        f"User question: {question}\n\nSQL:"
    )
    llm = get_llm()
    sql = await llm.complete(prompt)
    # strip code fences or explanations if any slipped through
    sql = re.sub(r"^```sql|```$|^```|```$", "", sql.strip(), flags=re.I|re.M).strip()
    # ensure semicolon at end
    if not sql.endswith(";"):
        sql += ";"
    return sql
  
