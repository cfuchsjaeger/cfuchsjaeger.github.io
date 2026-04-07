from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .listing import ListingResponse


class DealBase(BaseModel):
    listing_id: int
    deal_score: float
    market_price: Optional[float] = None
    price_difference: Optional[float] = None
    price_difference_pct: Optional[float] = None
    ai_analysis: Optional[str] = None
    ai_recommendation: Optional[str] = None
    is_notified: bool = False


class DealCreate(DealBase):
    pass


class DealUpdate(BaseModel):
    deal_score: Optional[float] = None
    market_price: Optional[float] = None
    price_difference: Optional[float] = None
    price_difference_pct: Optional[float] = None
    ai_analysis: Optional[str] = None
    ai_recommendation: Optional[str] = None
    is_notified: Optional[bool] = None


class DealResponse(DealBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DealWithListingResponse(DealResponse):
    listing: Optional[ListingResponse] = None

    class Config:
        from_attributes = True
