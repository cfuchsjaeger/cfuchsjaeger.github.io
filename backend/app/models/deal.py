from sqlalchemy import Column, Integer, Float, Boolean, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    deal_score = Column(Float, nullable=False)  # 0-1
    market_price = Column(Float, nullable=True)
    price_difference = Column(Float, nullable=True)  # market - listing price
    price_difference_pct = Column(Float, nullable=True)
    ai_analysis = Column(String, nullable=True)
    ai_recommendation = Column(String, nullable=True)  # buy/watch/skip
    is_notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("Listing", back_populates="deals")
    alerts = relationship("Alert", back_populates="deal", cascade="all, delete-orphan")
