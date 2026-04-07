from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from ..database import Base


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String, nullable=False, index=True)
    model = Column(String, nullable=False, index=True)
    reference_number = Column(String, nullable=True)
    average_price = Column(Float, nullable=False)
    min_price = Column(Float, nullable=False)
    max_price = Column(Float, nullable=False)
    sample_count = Column(Integer, nullable=False, default=0)
    source = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
