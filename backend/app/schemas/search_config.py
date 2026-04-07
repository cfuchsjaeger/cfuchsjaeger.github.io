from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SearchConfigBase(BaseModel):
    name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    keywords: Optional[str] = None
    sources: List[str] = ["willhaben", "chrono24"]
    is_active: bool = True


class SearchConfigCreate(SearchConfigBase):
    pass


class SearchConfigUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    keywords: Optional[str] = None
    sources: Optional[List[str]] = None
    is_active: Optional[bool] = None


class SearchConfigResponse(SearchConfigBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
