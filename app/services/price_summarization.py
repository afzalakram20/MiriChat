from app.core.config import settings
import json
from typing import List, Dict, Any
from openai import OpenAI
import logging
from datetime import date
from app.graphs.nodes.prompts.price_summary_system_prompt import PRICE_SUMMARY_SYSTEM_PROMPT
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.llms.runnable.llm_provider import get_chain_llm
log = logging.getLogger("app.services.price_summarization")

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def summarize_tavily_results_with_llm(
    tavily_results: List[Dict[str, Any]],
    country: str,
    city: str
):
    """
    Second-stage LLM call:
    - Input: Tavily search results + FX rates
    - Output: list of {url, title, content, minimum-cost, maximum-cost} with prices in USD.
    """
    log.info("summarize_tavily_results_with_llm: %s", tavily_results)

    payload = {
        "additional_information": f"The extracted information should relate to {country} and {city} and the current date is {date.today().isoformat()}",
        "results": tavily_results,
    }
    log.info("payload: %s", payload)

    # Build LCEL chain with prompt -> llm -> text
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_text}"),
            ("user", "{payload_json}"),
        ]
    )
    llm = get_chain_llm()
    chain = prompt | llm | StrOutputParser()

    content = chain.invoke(
        {
            "system_text": PRICE_SUMMARY_SYSTEM_PROMPT,
            "payload_json": json.dumps(payload, ensure_ascii=False)
        }
    )
    log.info("content: %s", content)
    result_array = json.loads(content)
    log.info("result_array: %s", result_array)

    # Ensure it's a list
    # if not isinstance(result_array, list):
    #     raise ValueError("LLM did not return a JSON array")

    return result_array
