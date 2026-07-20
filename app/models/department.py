from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class DepartmentModelIn(BaseModel):
    name: str
    email: Optional[str] = None



class DepartmentModelOut(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    create_datetime: datetime
    update_datetime: datetime

    class Config:
        from_attributes = True
