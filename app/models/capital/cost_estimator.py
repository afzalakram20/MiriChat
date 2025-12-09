from pydantic import BaseModel, Field
from typing import Optional, List


class ScopeRequest(BaseModel):
    scope_text: str = Field(..., description="Full scope of work text")
    location_country: str = Field(
        ..., description="Country where equipment will be used"
    )
    location_city: Optional[str] = Field(
        None, description="City where equipment will be used"
    )
    currency: str = Field(
        "USD", description="Preferred currency for estimation (e.g., 'SAR', 'USD')"
    )


class PriceSource(BaseModel):
    title: str
    url: str
    raw_snippet: str
    observed_price: Optional[float] = None
    currency: Optional[str] = None


class ItemEstimate(BaseModel):
    name: str
    category: str
    brand: Optional[str]
    specification: str
    quantity: float
    unit_of_measure: str

    unit_price: Optional[float] = None
    currency: Optional[str] = None
    total_price: Optional[float] = None

    price_sources: List[PriceSource] = []
    notes: Optional[str] = None


class EstimationResponse(BaseModel):
    items: List[ItemEstimate]


class PurchaseItem(BaseModel):
    name: str
    category: str
    brand: Optional[str] = None
    specification: str
    quantity: float
    unit_of_measure: str


class MaterialExtractionResult(BaseModel):
    items: List[PurchaseItem]


class PriceSource(BaseModel):
    title: str
    url: str
    raw_snippet: str
    observed_price: Optional[float] = None
    currency: Optional[str] = None
