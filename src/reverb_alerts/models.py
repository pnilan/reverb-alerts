from enum import Enum

from pydantic import BaseModel, HttpUrl


class ReverbCondition(str, Enum):
    BRAND_NEW = "Brand New"
    MINT = "Mint"
    EXCELLENT = "Excellent"
    VERY_GOOD = "Very Good"
    GOOD = "Good"
    B_STOCK = "B-Stock"
    POOR = "Poor Condition"
    NON_FUNCTIONING = "Non Functioning"


class ReverbListing(BaseModel):
    title: str
    price: float
    shipping_cost: float | None = None
    seller_location: str | None = None
    url: HttpUrl
    condition: ReverbCondition | None = None
