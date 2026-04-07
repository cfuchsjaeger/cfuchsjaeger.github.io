from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models.listing import Listing
from ..schemas.listing import ListingResponse, ListingUpdate

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("", response_model=List[ListingResponse])
def get_listings(
    source: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Listing)
    if source:
        query = query.filter(Listing.source == source)
    if brand:
        query = query.filter(Listing.brand.ilike(f"%{brand}%"))
    if is_active is not None:
        query = query.filter(Listing.is_active == is_active)
    return query.order_by(Listing.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{listing_id}", response_model=ListingResponse)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.put("/{listing_id}", response_model=ListingResponse)
def update_listing(
    listing_id: int,
    data: ListingUpdate,
    db: Session = Depends(get_db),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(listing, field, value)
    db.commit()
    db.refresh(listing)
    return listing


@router.delete("/{listing_id}")
def delete_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    db.delete(listing)
    db.commit()
    return {"message": "Listing deleted"}
