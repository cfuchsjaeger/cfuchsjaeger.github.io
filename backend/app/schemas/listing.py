from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ListingBase(BaseModel):
    external_id: str
    source: str
    title: str
    brand: Optional[str] = None
    model: Optional[str] = None
    reference_number: Optional[str] = None
    price: float
    currency: str = "EUR"
    condition: Optional[str] = None
    year: Optional[int] = None
    description: Optional[str] = None
    url: str
    image_urls: Optional[List[str]] = None
    location: Optional[str] = None
    seller_name: Optional[str] = None
    is_active: bool = True


class ListingCreate(ListingBase):
    pass


class ListingUpdate(BaseModel):
    title: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    reference_number: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    condition: Optional[str] = None
    year: Optional[int] = None
    description: Optional[str] = None
    url: Optional[str] = None
    image_urls: Optional[List[str]] = None
    location: Optional[str] = None
    seller_name: Optional[str] = None
    is_active: Optional[bool] = None


class ListingResponse(ListingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
