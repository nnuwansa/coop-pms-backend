from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel


class OrderByOptionIn(BaseModel):
    name: str
    category: Literal['role', 'action'] = 'action'   # NEW


class OrderByOptionUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[Literal['role', 'action']] = None   # NEW
    is_active: Optional[bool] = None


class OrderByOptionOut(BaseModel):
    id: int
    name: str
    category: str   # NEW
    is_active: bool
    create_datetime: datetime

    class Config:
        from_attributes = True