from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    qualities = relationship("PositionQuality", back_populates="position", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="position", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Position(id={self.id}, title='{self.title}', is_active={self.is_active})>" 