from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, field_validator


class LetterUploadOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    file_size: Optional[int] = None
    url: str
    uploaded_by: str
    uploaded_by_id: int
    create_datetime: datetime

    @field_validator('create_datetime', mode='after')
    @classmethod
    def ensure_timezone(cls, value):
        return value.replace(tzinfo=timezone.utc)