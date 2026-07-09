from datetime import datetime

from pydantic import BaseModel


class SourceModelIn(BaseModel):
    name: str
    code: str | None = None


class SourceModelOut(BaseModel):
    id: int
    name: str
    code: str | None = None
    create_datetime: datetime
    update_datetime: datetime

    class Config:
        from_attributes = True
