from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class EmployeeNameModelIn(BaseModel):
    full_name: str


class EmployeeNameModelUpdate(BaseModel):
    full_name: str
    is_active: Optional[bool] = True


class EmployeeNameModelOut(BaseModel):
    id: int
    full_name: str
    is_active: bool
    update_datetime: datetime
    create_datetime: datetime

    class Config:
        from_attributes = True