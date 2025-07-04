from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatBase(BaseModel):
    title: Optional[str] = None
    chat_type: str = "private"  # 'private', 'group', 'channel'
    description: Optional[str] = None
    photo_url: Optional[str] = None


class ChatCreate(ChatBase):
    member_ids: List[int] = []  # ID пользователей для добавления в чат


class ChatUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    photo_url: Optional[str] = None


class UserInChat(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    profile_photo_url: Optional[str]
    is_admin: bool = False
    joined_at: datetime
    
    class Config:
        from_attributes = True


class Chat(ChatBase):
    id: int
    created_by: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    members: List[UserInChat] = []
    
    class Config:
        from_attributes = True


class ChatList(BaseModel):
    id: int
    title: Optional[str]
    chat_type: str
    photo_url: Optional[str]
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int = 0
    
    class Config:
        from_attributes = True


class InviteByUsernameRequest(BaseModel):
    username: str 