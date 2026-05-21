from datetime import datetime, timezone

from pydantic import BaseModel, field_validator


class HistoryModelOut(BaseModel):
    id: int
    description: str
    username: str
    email: str
    create_datetime: datetime
    letter_id: int

    @field_validator('create_datetime', mode='after')
    @classmethod
    def ensure_timezone(cls, value):
        return value.replace(tzinfo=timezone.utc)

    class Config:
        from_attributes = True
