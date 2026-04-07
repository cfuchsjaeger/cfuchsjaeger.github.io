from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MarketPriceBase(BaseModel):
    brand: str
    model: str
    reference_number: Optional[str] = None
    average_price: float
    min_price: float
    max_price: float
    sample_count: int = 0
    source: str


class MarketPriceCreate(MarketPriceBase):
    pass


class MarketPriceUpdate(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    reference_number: Optional[str] = None
    average_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    sample_count: Optional[int] = None
    source: Optional[str] = None


class MarketPriceResponse(MarketPriceBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True
