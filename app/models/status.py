from datetime import datetime

from pydantic import BaseModel


class StatusModelIn(BaseModel):
    name: str


class StatusModelOut(StatusModelIn):
    id: int
    name: str
    create_datetime: datetime
    update_datetime: datetime

    class Config:
        from_attributes = True
