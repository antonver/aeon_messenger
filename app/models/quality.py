from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Quality(Base):
    __tablename__ = "qualities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Связи
    position_qualities = relationship("PositionQuality", back_populates="quality", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Quality(id={self.id}, name='{self.name}')>" 