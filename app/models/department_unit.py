from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DepartmentUnitModelIn(BaseModel):
    name: str
    email: Optional[str] = None

class DepartmentUnitModelOut(BaseModel):
    id: int
    department_id: int
    name: str
    email: Optional[str] = None
    create_datetime: datetime
    update_datetime: datetime

    class Config:
        from_attributes = True