from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# Промежуточная таблица для связи многие-ко-многим между пользователями и чатами
chat_members = Table(
    'chat_members',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('chat_id', Integer, ForeignKey('chats.id'), primary_key=True),
    Column('joined_at', DateTime(timezone=True), server_default=func.now()),
    Column('is_admin', Boolean, default=False)
)


class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)  # Для групповых чатов
    chat_type = Column(String, nullable=False)  # 'private', 'group', 'channel'
    description = Column(Text, nullable=True)
    photo_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Отношения
    creator = relationship("User", foreign_keys=[created_by])
    members = relationship("User", secondary=chat_members, back_populates="chats")
    messages = relationship("Message", foreign_keys="Message.chat_id", back_populates="chat", cascade="all, delete-orphan") 