from datetime import datetime

from pydantic import BaseModel


class SourceModelIn(BaseModel):
    name: str


class SourceModelOut(BaseModel):
    id: int
    name: str
    create_datetime: datetime
    update_datetime: datetime

    class Config:
        from_attributes = True
