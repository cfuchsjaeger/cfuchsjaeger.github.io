from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models.search_config import SearchConfig
from ..schemas.search_config import (
    SearchConfigCreate,
    SearchConfigUpdate,
    SearchConfigResponse,
)

router = APIRouter(prefix="/search-configs", tags=["search_configs"])


@router.get("", response_model=List[SearchConfigResponse])
def get_search_configs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return db.query(SearchConfig).order_by(SearchConfig.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=SearchConfigResponse)
def create_search_config(data: SearchConfigCreate, db: Session = Depends(get_db)):
    config = SearchConfig(**data.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.get("/{config_id}", response_model=SearchConfigResponse)
def get_search_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(SearchConfig).filter(SearchConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Search config not found")
    return config


@router.put("/{config_id}", response_model=SearchConfigResponse)
def update_search_config(
    config_id: int,
    data: SearchConfigUpdate,
    db: Session = Depends(get_db),
):
    config = db.query(SearchConfig).filter(SearchConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Search config not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(config, field, value)
    db.commit()
    db.refresh(config)
    return config


@router.delete("/{config_id}")
def delete_search_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(SearchConfig).filter(SearchConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Search config not found")
    db.delete(config)
    db.commit()
    return {"message": "Search config deleted"}


@router.post("/{config_id}/toggle-active", response_model=SearchConfigResponse)
def toggle_search_config_active(config_id: int, db: Session = Depends(get_db)):
    config = db.query(SearchConfig).filter(SearchConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Search config not found")
    config.is_active = not config.is_active
    db.commit()
    db.refresh(config)
    return config
