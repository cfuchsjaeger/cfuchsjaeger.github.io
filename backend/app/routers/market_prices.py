from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models.market_price import MarketPrice
from ..schemas.market_price import MarketPriceCreate, MarketPriceUpdate, MarketPriceResponse

router = APIRouter(prefix="/market-prices", tags=["market_prices"])


@router.get("", response_model=List[MarketPriceResponse])
def get_market_prices(
    brand: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(MarketPrice)
    if brand:
        query = query.filter(MarketPrice.brand.ilike(f"%{brand}%"))
    return query.order_by(MarketPrice.brand, MarketPrice.model).offset(skip).limit(limit).all()


@router.post("", response_model=MarketPriceResponse)
def create_market_price(data: MarketPriceCreate, db: Session = Depends(get_db)):
    mp = MarketPrice(**data.model_dump())
    db.add(mp)
    db.commit()
    db.refresh(mp)
    return mp


@router.put("/{mp_id}", response_model=MarketPriceResponse)
def update_market_price(
    mp_id: int,
    data: MarketPriceUpdate,
    db: Session = Depends(get_db),
):
    mp = db.query(MarketPrice).filter(MarketPrice.id == mp_id).first()
    if not mp:
        raise HTTPException(status_code=404, detail="Market price not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(mp, field, value)
    db.commit()
    db.refresh(mp)
    return mp


@router.delete("/{mp_id}")
def delete_market_price(mp_id: int, db: Session = Depends(get_db)):
    mp = db.query(MarketPrice).filter(MarketPrice.id == mp_id).first()
    if not mp:
        raise HTTPException(status_code=404, detail="Market price not found")
    db.delete(mp)
    db.commit()
    return {"message": "Market price deleted"}
