from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from ..database import get_db
from ..models.deal import Deal
from ..models.listing import Listing
from ..schemas.deal import DealResponse, DealWithListingResponse
from ..services.ai_analyzer import AIAnalyzer
from ..config import settings

router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("", response_model=List[DealWithListingResponse])
def get_deals(
    min_score: Optional[float] = Query(None, ge=0, le=1),
    recommendation: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Deal).options(joinedload(Deal.listing))
    if min_score is not None:
        query = query.filter(Deal.deal_score >= min_score)
    if recommendation:
        query = query.filter(Deal.ai_recommendation == recommendation)
    return query.order_by(Deal.deal_score.desc()).offset(skip).limit(limit).all()


@router.get("/{deal_id}", response_model=DealWithListingResponse)
def get_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = (
        db.query(Deal)
        .options(joinedload(Deal.listing))
        .filter(Deal.id == deal_id)
        .first()
    )
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.post("/{deal_id}/analyze", response_model=DealWithListingResponse)
async def analyze_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = (
        db.query(Deal)
        .options(joinedload(Deal.listing))
        .filter(Deal.id == deal_id)
        .first()
    )
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="AI analyzer not configured")

    analyzer = AIAnalyzer(api_key=settings.ANTHROPIC_API_KEY)
    listing = deal.listing

    listing_data = {
        "title": listing.title,
        "brand": listing.brand,
        "model": listing.model,
        "reference_number": listing.reference_number,
        "price": listing.price,
        "condition": listing.condition,
        "year": listing.year,
        "source": listing.source,
        "location": listing.location,
        "description": listing.description,
    }

    deal_data = {
        "deal_score": deal.deal_score,
        "price_difference": deal.price_difference,
        "price_difference_pct": deal.price_difference_pct,
    }

    try:
        result = await analyzer.analyze_deal(listing_data, deal_data, None)
        deal.ai_analysis = result.get("analysis", "")
        deal.ai_recommendation = result.get("recommendation", "watch")
        db.commit()
        db.refresh(deal)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    return deal
