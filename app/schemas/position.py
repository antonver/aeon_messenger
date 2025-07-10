from pydantic import BaseModel
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .quality import Quality

class PositionBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_active: bool = True

class PositionCreate(PositionBase):
    quality_ids: Optional[List[int]] = []

class PositionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Position(PositionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PositionWithQualities(Position):
    qualities: List["Quality"] = []
    
    class Config:
        from_attributes = True 