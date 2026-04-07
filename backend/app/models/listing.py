from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True, nullable=False)
    source = Column(String, nullable=False)  # willhaben / chrono24
    title = Column(String, nullable=False)
    brand = Column(String, nullable=True)
    model = Column(String, nullable=True)
    reference_number = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    currency = Column(String, default="EUR")
    condition = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    description = Column(String, nullable=True)
    url = Column(String, nullable=False)
    image_urls = Column(JSON, nullable=True)
    location = Column(String, nullable=True)
    seller_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    deals = relationship("Deal", back_populates="listing", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="listing", cascade="all, delete-orphan")
