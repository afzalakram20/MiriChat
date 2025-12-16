from app.services.price_summarization import summarize_tavily_results_with_llm
from app.services.pricing import parse_price_candidates
import json

from openai import OpenAI
from app.core.config import settings
from app.models.capital.cost_estimator import MaterialExtractionResult, ScopeRequest
import logging
import os

from app.core.config import settings
from app.graphs.nodes.prompts.material_extraction_system_prompt import MATERIAL_EXTRACTION_SYSTEM_PROMPT
log = logging.getLogger("app.services.cost_estimator")

client = OpenAI(api_key=settings.OPENAI_API_KEY)
import re
from typing import List, Tuple, Optional
from statistics import median

from tavily import TavilyClient
from app.models.capital.cost_estimator import (
    ScopeRequest,
    PurchaseItem,
    ItemEstimate,
    PriceSource,
)

from app.llms.runnable.llm_provider import get_chain_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
class CostEstimatorService:
    async def llm_extract_materials(
        self, req: ScopeRequest, model_key: Optional[str] = None, model_id: Optional[str] = None
    ) -> MaterialExtractionResult:
        """
        Uses GPT-5.1 to extract purchasable items from a scope of work,
        returning a MaterialExtractionResult (list of PurchaseItem).
        """
        log.info("llm_extract_materials %s", req)
        log.info("llm_extract_materials  scope of work%s", req["scope_text"])
        log.info("llm_extract_materials  location country%s", req["location_country"])
        log.info("llm_extract_materials  location city%s", req["location_city"])
        log.info("llm_extract_materials  currency%s", req["currency"])
        user_prompt = build_material_extraction_user_prompt(
            scope_text=req["scope_text"],
            location_country=req["location_country"],
            location_city=req["location_city"],
            currency=req["currency"],
        )
        log.info(f"user_prompt: {user_prompt}")

        # Build LCEL chain with prompt -> llm -> parser
        parser = PydanticOutputParser(pydantic_object=MaterialExtractionResult)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_text}"),
                ("user", "{user_prompt}"),
            ]
        )
        llm = get_chain_llm(model_key, model_id)
        chain = prompt | llm | parser

        result: MaterialExtractionResult = await chain.ainvoke(
            {
                "system_text": MATERIAL_EXTRACTION_SYSTEM_PROMPT,
                "user_prompt": user_prompt
            }
        )
        return result


def build_material_extraction_user_prompt(
    scope_text: str,
    location_country: str,
    location_city: str | None,
    currency: str,
) -> str:
    return f"""
You will receive a scope of work and some context.

LOCATION COUNTRY: {location_country}
LOCATION CITY: {location_city or "null"}
CURRENCY: {currency}

SCOPE OF WORK:
\"\"\" 
{scope_text}
\"\"\"

Return ONLY the extracted items as a JSON object according to the schema described in the system message.
"""


TAVILY_API_KEY = os.getenv(
    "TAVILY_API_KEY", "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"
)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


def build_tavily_query(item: PurchaseItem, req: ScopeRequest):
    parts: list[str] = []
    if item.brand:
        parts.append(item.brand)
    if item.category:
        parts.append(item.category)
    if item.specification:
        parts.append(item.specification)
    parts.append("price")
    parts.append(req["location_country"])
    if req["location_city"]:
        parts.append(req["location_city"])

    return " ".join(p for p in parts if p).strip()


def estimate_price_for_item(
    item: PurchaseItem,
    req: ScopeRequest,
    client: TavilyClient | None = None,
):
    """
    Calls Tavily, extracts numeric prices from snippets, and returns an ItemEstimate
    with unit_price / total_price and price_sources filled.
    """
    log.info(f"Estimating price for item: {item}")
    tvly = client or tavily_client
    log.info(f"Tavily client: {tvly}")

    query = build_tavily_query(item, req)
    log.info(f"Tavily query: {query}")

    # Tavily search parameters – adjust as needed
    response = tvly.search(
        query=query,
        search_depth="advanced",  # better recall
        max_results=5,
        include_answer=False,
        include_raw_content=False,
        topic="general",
    )
    log.info(f"Tavily response: {response}")

    results = response.get("results", [])
    log.info(f"Tavily search results: {results}")
    price_sources: list[PriceSource] = []
    prices_list: list[float] = []
    candidate_currencies: list[str] = []
    prices_data = summarize_tavily_results_with_llm(
        results, req["location_country"], req["location_city"]
    )
    prices_data_composed = {
        "name": item.name,
        "search_query": query,  # query comes from your function, not the item
        "category": item.category,
        "brand": item.brand,
        "specification": item.specification,
        "quantity": item.quantity,
        "unit_of_measure": item.unit_of_measure,
        "items": prices_data,  # make sure this is a list of plain dicts
    }
    log.info(f"prices_data AFTER: {prices_data_composed}")

    # for r in results:
    #     title = r.get("title", "") or ""
    #     url = r.get("url", "") or ""
    #     content = r.get("content", "") or ""
    #     log.info(f"Tavily search result: {r}")
    #     fx_to_usd = {"USD": 1.0, "PKR": 0.0026315}
    #     prices_data = summarize_tavily_results_with_llm(r, fx_to_usd, "USD")
    #     log.info(f"Prices: {prices_data}")
    #     prices_list.append(prices_data)
    #     log.info(f"Prices list: {prices_list}")

    return prices_data_composed
