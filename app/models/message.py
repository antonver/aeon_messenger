from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey('chats.id'), nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Содержимое сообщения
    text = Column(Text, nullable=True)
    message_type = Column(String, default='text')  # 'text', 'photo', 'video', 'audio', 'voice', 'document', 'sticker'
    
    # Медиа файлы
    media_url = Column(String, nullable=True)
    media_type = Column(String, nullable=True)  # 'image/jpeg', 'video/mp4', 'audio/mp3', etc.
    media_size = Column(Integer, nullable=True)
    media_duration = Column(Integer, nullable=True)  # для аудио/видео в секундах
    
    # Дополнительные данные
    reply_to_message_id = Column(Integer, ForeignKey('messages.id'), nullable=True)
    forward_from_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    forward_from_chat_id = Column(Integer, ForeignKey('chats.id'), nullable=True)
    
    # Метаданные
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    read_by = Column(JSON, default=list)  # список user_id, которые прочитали сообщение
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Отношения
    chat = relationship("Chat", foreign_keys=[chat_id], back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    reply_to = relationship("Message", remote_side=[id])
    forward_from_user = relationship("User", foreign_keys=[forward_from_user_id])
    forward_from_chat = relationship("Chat", foreign_keys=[forward_from_chat_id]) 