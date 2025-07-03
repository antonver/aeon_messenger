from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class MessageBase(BaseModel):
    text: Optional[str] = None
    message_type: str = "text"  # 'text', 'photo', 'video', 'audio', 'voice', 'document', 'sticker'
    reply_to_message_id: Optional[int] = None


class MessageCreate(MessageBase):
    chat_id: int


class MessageUpdate(BaseModel):
    text: Optional[str] = None


class MessageSender(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    profile_photo_url: Optional[str]
    
    class Config:
        from_attributes = True


class Message(MessageBase):
    id: int
    chat_id: int
    sender_id: int
    sender: MessageSender
    
    # Медиа файлы
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    media_size: Optional[int] = None
    media_duration: Optional[int] = None
    
    # Дополнительные данные
    forward_from_user_id: Optional[int] = None
    forward_from_chat_id: Optional[int] = None
    
    # Метаданные
    is_edited: bool = False
    is_deleted: bool = False
    read_by: List[int] = []
    
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class MessageList(BaseModel):
    messages: List[Message]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool 