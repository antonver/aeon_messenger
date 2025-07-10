from pydantic import BaseModel
from typing import Optional

class QualityBase(BaseModel):
    name: str
    description: Optional[str] = None

class QualityCreate(QualityBase):
    pass

class QualityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class Quality(QualityBase):
    id: int
    
    class Config:
        from_attributes = True 