# pricing.py
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

# --- Price parsing helpers ---

CURRENCY_MAP = {
    "sar": "SAR",
    "ر.س": "SAR",
    "$": "USD",
    "usd": "USD",
    "€": "EUR",
    "eur": "EUR",
    "£": "GBP",
    "gbp": "GBP",
    "aed": "AED",
    "qar": "QAR",
    "rs": "PKR",
    "pkr": "PKR",
}

PRICE_PATTERNS = [
    re.compile(
        r"(?P<currency>SAR|USD|EUR|GBP|AED|QAR|PKR|Rs\.?|ر\.س|\$|€|£)\s*(?P<amount>[0-9][0-9,\.]*)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?P<amount>[0-9][0-9,\.]*)\s*(?P<currency>SAR|USD|EUR|GBP|AED|QAR|PKR|Rs\.?|ر\.س|\$|€|£)",
        re.IGNORECASE,
    ),
]


def normalize_currency(symbol: str) -> Optional[str]:
    key = symbol.strip().lower()
    return CURRENCY_MAP.get(key)


def parse_price_candidates(text: str) -> List[Tuple[float, Optional[str]]]:
    candidates: List[Tuple[float, Optional[str]]] = []
    for pattern in PRICE_PATTERNS:
        for m in pattern.finditer(text):
            amount_str = m.group("amount")
            currency_symbol = m.group("currency")
            try:
                amount = float(amount_str.replace(",", ""))
            except ValueError:
                continue
            currency = normalize_currency(currency_symbol) or currency_symbol.upper()
            candidates.append((amount, currency))
    return candidates
