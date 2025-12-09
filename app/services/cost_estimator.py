from app.services.price_summarization import summarize_tavily_results_with_llm
from app.services.pricing import parse_price_candidates
import json

from openai import OpenAI
from app.core.config import settings
from app.models.capital.cost_estimator import MaterialExtractionResult, ScopeRequest
import logging
import os

from app.core.config import settings

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


class CostEstimatorService:
    async def llm_extract_materials(
        self, req: ScopeRequest
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

        completion = client.chat.completions.create(
            model="gpt-5.1",
            messages=[
                {"role": "system", "content": MATERIAL_EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,  # deterministic as much as possible
            response_format={"type": "json_object"},  # force JSON
        )

        raw_content = completion.choices[0].message.content
        log.info(f"raw_content: {raw_content}")
        data = json.loads(raw_content)
        log.info(f"data: {data}")

        return MaterialExtractionResult(**data)


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


# prompts.py

MATERIAL_EXTRACTION_SYSTEM_PROMPT = """
You are a cost estimation assistant.

Your ONLY job is to read a scope of work and extract a list of NEW items that must be PURCHASED (materials or equipment).
You MUST return STRICTLY VALID JSON that matches this schema:

{
  "items": [
    {
      "name": "string, human readable item name",
      "search_query": "string, the query to search for the item from search engine",
      "category": "string, generic category such as 'generator', 'cable', 'panel', 'pump', 'valve'",
      "brand": "string or null, brand name if specified or clearly implied (e.g. 'Caterpillar')",
      "specification": "string, key technical spec or description, e.g. '100 kVA diesel generator', '4C 240mm2 XLPE/PVC copper cable'",
      "quantity": "number, the quantity to purchase (use 1 if not specified)",
      "unit_of_measure": "string, e.g. 'unit', 'piece', 'meter', 'set'"
    }
  ]
}

CRITICAL RULES:
- Only include NEW items that must be PURCHASED.
- Do NOT include labor or services like installation, testing, commissioning, programming, logistics, etc.
- Do NOT list existing equipment that is just being relocated, repaired, or reused.
- If the brand name is misspelled in the text, fix it to the correct brand spelling (e.g. 'caterpiler' -> 'Caterpillar') where obvious.
- If quantity is not mentioned, assume quantity = 1.
- If unit is not clear, use 'unit'.
- If no purchasable items are found, return {"items": []}.
- Your response MUST be ONLY the JSON object, with no explanation, no comments, and no extra text.
- Make the search_query such that it can be used to search for the item from search engine with high accuracy.
- Always make sure that the search_query is such that it should search latest prices with mentioned city and country.

EXAMPLES:

Example 1
---------
SCOPE OF WORK:
"The existing generator is undersized. We will supply and install a new Caterpillar diesel generator 100kVA with acoustic enclosure, and connect it to the existing MDB. Supply all necessary materials."

Expected JSON:
{
  "items": [
    {
      "name": "Caterpillar diesel generator",
      "search_query": "today price for Caterpillar diesel generator 100kVA in New York USA",
      "category": "generator",
      "brand": "Caterpillar",
      "specification": "100 kVA standby diesel generator with acoustic enclosure",
      "quantity": 1,
      "unit_of_measure": "unit"
    }
  ]
}

Example 2
---------
SCOPE OF WORK:
"Provide and install 200m of 4C 240mm2 XLPE/PVC copper power cable from MDB-A to Generator, including all lugs and terminations. Testing and commissioning by contractor."

Expected JSON:
{
  "items": [
    {
      "name": "4-core 240mm2 XLPE/PVC copper power cable",
      "search_query": "today price for 4-core 240mm2 XLPE/PVC copper power cable in New York USA",
      "category": "cable",
      "brand": null,
      "specification": "4C 240mm2 XLPE/PVC copper power cable",
      "quantity": 200,
      "unit_of_measure": "meter"
    },
    {
      "name": "Cable lugs and terminations for 4C 240mm2 cable",
      "search_query": "today price for Cable lugs and terminations for 4C 240mm2 cable in New York",
      "category": "accessories",
      "brand": null,
      "specification": "Cable lugs and terminations compatible with 4C 240mm2 power cable",
      "quantity": 1,
      "unit_of_measure": "set"
    }
  ]
}

Example 3
---------
SCOPE OF WORK:
"Test and commission the existing 100 kVA generator and clean the fuel tank. No new equipment is required."

Expected JSON:
{
  "items": []
}

Example 4
---------
SCOPE OF WORK:
"the system may be expire so we will have to install caterpiler generator of 100kva"

Expected JSON:
{
  "items": [
    {
      "name": "Caterpillar diesel generator",
      "search_query": "today price for Caterpillar diesel generator 100kVA in New York",
      "category": "generator",
      "brand": "Caterpillar",
      "specification": "100 kVA diesel generator",
      "quantity": 1,
      "unit_of_measure": "unit"
    }
  ]
}
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
