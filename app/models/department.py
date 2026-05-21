from datetime import datetime

from pydantic import BaseModel


class DepartmentModelIn(BaseModel):
    name: str


class DepartmentModelOut(BaseModel):
    id: int
    name: str
    create_datetime: datetime
    update_datetime: datetime

    class Config:
        from_attributes = True
