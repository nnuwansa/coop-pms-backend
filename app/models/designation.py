from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DesignationModelIn(BaseModel):
    name: str
    description: Optional[str] = None


class DesignationModelUpdate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: Optional[bool] = True


class DesignationModelOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    update_datetime: datetime
    create_datetime: datetime

    class Config:
        from_attributes = True