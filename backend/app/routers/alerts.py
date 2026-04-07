from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.alert import Alert
from ..schemas.alert import AlertResponse, AlertStats

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertResponse])
def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return (
        db.query(Alert)
        .order_by(Alert.sent_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/stats", response_model=AlertStats)
def get_alert_stats(db: Session = Depends(get_db)):
    total = db.query(Alert).count()
    successful = db.query(Alert).filter(Alert.success == True).count()
    failed = db.query(Alert).filter(Alert.success == False).count()
    telegram = db.query(Alert).filter(Alert.channel == "telegram").count()

    return AlertStats(
        total_alerts=total,
        successful_alerts=successful,
        failed_alerts=failed,
        telegram_alerts=telegram,
    )
