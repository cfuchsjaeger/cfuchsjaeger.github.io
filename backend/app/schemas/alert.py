from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AlertBase(BaseModel):
    deal_id: int
    channel: str
    message: str
    success: bool


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    id: int
    sent_at: datetime

    class Config:
        from_attributes = True


class AlertStats(BaseModel):
    total_alerts: int
    successful_alerts: int
    failed_alerts: int
    telegram_alerts: int
