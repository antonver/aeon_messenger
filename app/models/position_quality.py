from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class PositionQuality(Base):
    __tablename__ = "position_qualities"
    
    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    quality_id = Column(Integer, ForeignKey("qualities.id"), nullable=False)
    weight = Column(Integer, default=1)  # Вес качества для генерации вопросов
    
    # Связи
    position = relationship("Position", back_populates="qualities")
    quality = relationship("Quality", back_populates="position_qualities")
    
    def __repr__(self):
        return f"<PositionQuality(position_id={self.position_id}, quality_id={self.quality_id}, weight={self.weight})>" 