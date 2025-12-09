# app/graphs/nodes/intent_node.py

import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from app.llms.runnable.llm_provider import get_chain_llm
import logging
log=logging.getLogger("intent_node")
from app.graphs.nodes.prompts.intent_prompt import SYSTEM_MESSAGE
from app.models.parsers.chat_node_parsers import IntentResult
 

# - "project_metadata"   → simple project info (BU, site, status, ID, filters)
parser = PydanticOutputParser(pydantic_object=IntentResult)


async def intent_node(state):
    log.info("*************landed into intent node*************")

    user_input = state["user_input"] 
    prompt = ChatPromptTemplate.from_messages([
                                ("system", SYSTEM_MESSAGE),
                                ("user",  "{user_input}")
                                ])
 
    llm = get_chain_llm() 
    chain=prompt | llm | parser 
    response=await chain.ainvoke({
        "user_input": user_input
    })

    log.info(f"generated response in intention---->{response}")
    try:
        parsed = response.dict()
        log.info(f"intention detected---->{parsed}")
    except:
        log.error(f"intention failed xxx")
        parsed = {
            "intent": "unknown",
            "post_actions": [],
            "params": {},
            "requires_multistep": False
        }

    # Fill into state
    state["intent"] = parsed.get("intent", "unknown")
    state["post_actions"] = parsed.get("post_actions", [])
    state["params"] = parsed.get("params", {})
    state["requires_multistep"] = parsed.get("requires_multistep", False)

    # Also normalize email presence for convenience
    state["email"] = "email" in state["post_actions"]
    state["export"] = "export" in state["post_actions"] or "download" in state["post_actions"]

    # Shortcut: store email_to
    if "email_to" in state["params"]:
        state["email_to"] = state["params"]["email_to"]

    return state
