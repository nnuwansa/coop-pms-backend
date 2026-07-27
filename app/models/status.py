from datetime import datetime

from pydantic import BaseModel


class StatusModelIn(BaseModel):
    name: str
    requires_file_name: bool = False  # NEW


class StatusModelOut(StatusModelIn):
    id: int
    name: str
    requires_file_name: bool = False  # NEW
    create_datetime: datetime
    update_datetime: datetime

    class Config:
        from_attributes = True
