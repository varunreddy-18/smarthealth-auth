from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    device = Column(String(200), nullable=True)
    browser = Column(String(500), nullable=True)
    ip_address = Column(String(100), nullable=True)

    login_time = Column(DateTime, default=datetime.utcnow)
    logout_time = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="sessions")