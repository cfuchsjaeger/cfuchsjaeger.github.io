from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models.price_history import PriceHistory
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/price-history", tags=["price_history"])


class PriceHistoryResponse(BaseModel):
    id: int
    listing_id: int
    price: float
    recorded_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[PriceHistoryResponse])
def get_price_history(
    listing_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(PriceHistory)
    if listing_id is not None:
        query = query.filter(PriceHistory.listing_id == listing_id)
    return (
        query.order_by(PriceHistory.recorded_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
