from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, field_validator


class ManagedFileIn(BaseModel):
    file_number: str
    department_id: int
    department_unit_id: Optional[int] = None
    subject: str
    assigned_to_id: Optional[int] = None


class ManagedFileOut(BaseModel):
    id: int
    file_number: str
    department_id: int
    department_name: str
    department_unit_id: Optional[int] = None
    department_unit_name: Optional[str] = None
    subject: str
    assigned_to_id: Optional[int] = None
    assigned_to_name: Optional[str] = None
    create_datetime: datetime

    @field_validator('create_datetime', mode='after')
    @classmethod
    def ensure_timezone(cls, value):
        return value.replace(tzinfo=timezone.utc)


class ManagedFileBrief(BaseModel):   # NEW — lighter shape for the "my files" picker
    id: int
    file_number: str
    subject: str