from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Interview(Base):
    __tablename__ = "interviews"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    status = Column(String(50), default="in_progress")  # in_progress, completed, cancelled
    score = Column(Integer)  # Общий балл
    max_score = Column(Integer, default=100)
    answers = Column(JSON)  # Ответы на вопросы
    questions = Column(JSON)  # Вопросы интервью
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Связи
    user = relationship("User", back_populates="interviews")
    position = relationship("Position", back_populates="interviews")
    
    def __repr__(self):
        return f"<Interview(id={self.id}, user_id={self.user_id}, position_id={self.position_id}, status='{self.status}', score={self.score})>" 