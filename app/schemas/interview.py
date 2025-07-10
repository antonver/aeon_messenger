from pydantic import BaseModel
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .user import User
    from .position import Position

class InterviewBase(BaseModel):
    position_id: int

class InterviewCreate(InterviewBase):
    pass

class InterviewUpdate(BaseModel):
    status: Optional[str] = None
    score: Optional[int] = None
    answers: Optional[Dict[str, Any]] = None
    questions: Optional[List[Dict[str, Any]]] = None
    completed_at: Optional[datetime] = None

class Interview(InterviewBase):
    id: int
    user_id: int
    status: str
    score: Optional[int] = None
    max_score: int
    answers: Optional[Dict[str, Any]] = None
    questions: Optional[List[Dict[str, Any]]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class InterviewWithUser(Interview):
    user: "User"
    position: "Position"
    
    class Config:
        from_attributes = True 