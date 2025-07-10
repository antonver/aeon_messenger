from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    language_code: Optional[str] = "en"
    is_premium: bool = False
    is_admin: bool = False
    profile_photo_url: Optional[str] = None
    bio: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    profile_photo_url: Optional[str] = None
    bio: Optional[str] = None
    is_admin: Optional[bool] = None


class SubordinateBase(BaseModel):
    subordinate_id: int


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    subordinates: List["User"] = []
    managers: List["User"] = []

    class Config:
        from_attributes = True


# Для избежания циклических импортов
User.model_rebuild()


class UserList(BaseModel):
    users: List[User]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool 