from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# Таблица для связи руководитель-подчиненный
subordinates_association = Table(
    'subordinates',
    Base.metadata,
    Column('manager_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('subordinate_id', Integer, ForeignKey('users.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    language_code = Column(String, default="en")
    is_premium = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    profile_photo_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Отношения
    chats = relationship("Chat", secondary="chat_members", back_populates="members")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    
    # Отношения руководитель-подчиненный
    subordinates = relationship(
        "User",
        secondary=subordinates_association,
        primaryjoin=id==subordinates_association.c.manager_id,
        secondaryjoin=id==subordinates_association.c.subordinate_id,
        backref="managers"
    )
    
    # Отношения для HR системы
    interviews = relationship("Interview", back_populates="user") 