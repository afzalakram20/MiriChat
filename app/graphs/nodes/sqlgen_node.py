from app.graphs.nodes.prompts.sql_gen_prompt import SECOND_SYSTEM_PROMPT
from app.models.parsers.text_to_sql_models import SchemaArgsModel
from app.mcp.tools.sql_node_tools import schema_tool
from app.graphs.nodes.prompts.sql_gen_prompt import FIRST_SYSTEM_PROMPT
from app.llms.runnable.llm_provider import get_chain_llm
import json
import re
import logging
from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from app.mcp.tools.sql_node_tools import tools
from app.controllers.tool_impl import tool_get_schema
from app.models.llm.factory import get_llm
from app.schemas.registry import SCHEMA_REGISTRY
from langchain_core.prompts import ChatPromptTemplate

log = logging.getLogger("graph>node>sqlgen")


# ============================================================
# KEEP YOUR EXISTING SQL PROMPTS
# ============================================================

SQL_HEADER = """
You are an expert MySQL SQL writer and data-security specialist.
Your job is to generate ONE and ONLY ONE ready-to-execute MySQL SELECT statement.
"""

SQL_RULES = """
Strict Technical Rules:
- Absolutely ONLY readonly SELECT statements.
- No INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE.
- No SELECT *.
- Only use columns that exist in the provided schema.
- LIMIT max 30.
- Only MySQL syntax.
"""

SQL_REASONING_RULES = """
After generating SQL, produce a manager-friendly explanation (2–4 sentences).
Avoid technical jargon.
Describe what the SQL retrieves & why it's useful for decisions.
"""


first_parser = PydanticOutputParser(pydantic_object=SchemaArgsModel)


async def sqlgen_node(state: Dict[str, Any]) -> Dict[str, Any]:
    log.info("landed in sql generation node 2 steps ")
    user_input = state["user_input"]

    llm = get_chain_llm()
    first_llm = llm
    first_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", FIRST_SYSTEM_PROMPT),
            ("user", "{user_input}"),
        ]
    )
    first_chain = first_prompt | first_llm | first_parser

    try:
        first_response = await first_chain.ainvoke({"user_input": user_input})
        log.info(f"The response for schema modules -> {first_response}")

        first_response_dict = first_response.dict()
        log.info(f"Parsed modules dict -> {first_response_dict}")

    except Exception as e:
        log.exception("Router schema extraction failed: %s", e)
        state["sql"] = None
        return state

    modules = first_response_dict["modules"]
    log.info(f"Extracted modules list -> {modules}")

    # ===========================================
    #  EXECUTE SCHEMA TOOL
    # ===========================================

    tool_result = await tool_get_schema(modules)
    log.info(f"the response after get schema from laravel {str(tool_result)[:5]}")

    # ===========================================
    # 3) SECOND CALL — SQL GENERATION
    # ===========================================

    schema_json = json.dumps(tool_result, indent=2)  # or tool_result["schema"], etc.

    sql_user_message = (
        "User Question:\n" + user_input + "\n\nDatabase Schema (JSON):\n" + schema_json
    )

    second_messages = [
        {"role": "system", "content": SECOND_SYSTEM_PROMPT},
        {"role": "user", "content": sql_user_message},
    ]

    try:
        sql_response = await llm.chat(second_messages)
        log.info(f"sql_response output: {sql_response}")
        sql_obj = json.loads(sql_response.content)
        sql_query = sql_obj["sql"]

    except Exception as e:
        log.exception("SQL generation failed: %s", e)
        state["sql"] = None
        return state

    sql_query = sql_query.strip()
    log.info(f"[SQLGEN] cleaned model output: {sql_query}")

    if not sql_query.endswith(";"):
        sql_query += ";"

    state["sql"] = sql_query
    return state
