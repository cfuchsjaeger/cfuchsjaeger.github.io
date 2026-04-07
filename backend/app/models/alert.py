from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    channel = Column(String, nullable=False)  # telegram
    message = Column(String, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, nullable=False)

    deal = relationship("Deal", back_populates="alerts")
