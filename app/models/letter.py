from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class LetterFilter(BaseModel):
    id: Optional[int] = None
    code: Optional[str] = None
    subject: Optional[str] = None
    department_id: Optional[int] = None
    assignee_id: Optional[int] = None
    status_id: Optional[int] = None
    organization_id: Optional[int] = None
    create_date_start: Optional[datetime] = None
    create_date_end: Optional[datetime] = None
    other: Optional[str] = None


class LetterModelIn(BaseModel):
    code: str
    received_datetime: datetime
    subject: Optional[str] = None
    other: Optional[str] = None
    content: Optional[str] = None
    sender: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    source_id: Optional[int] = None
    organization_id: Optional[int] = None


class LetterModelOut(BaseModel):
    id: int
    code: str
    received_datetime: datetime
    create_datetime: datetime
    subject: Optional[str]
    other: Optional[str]
    sender: Optional[str]
    email: Optional[str]
    telephone: Optional[str]
    source_id: Optional[int]
    organization_id: Optional[int]

    @field_validator('received_datetime', 'create_datetime', mode='after')
    @classmethod
    def ensure_timezone(cls, value):
        return value.replace(tzinfo=timezone.utc)

    class Config:
        from_attributes = True


class AttachmentModelOut(BaseModel):
    id: int
    filename: str
    title: str
    create_datetime: datetime
    url: str

    @field_validator('create_datetime', mode='after')
    @classmethod
    def ensure_timezone(cls, value):
        return value.replace(tzinfo=timezone.utc)


class RemarksModelOut(BaseModel):
    id: int
    content: str
    create_datetime: datetime
    department: Optional[str]
    status: Optional[str]
    assignee: Optional[str]
    attachments: list[AttachmentModelOut]

    @field_validator('create_datetime', mode='after')
    @classmethod
    def ensure_timezone(cls, value):
        return value.replace(tzinfo=timezone.utc)


class IdNameModelOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class LetterModelOutOne(BaseModel):
    id: int
    code: str
    received_datetime: datetime
    create_datetime: datetime
    subject: Optional[str]
    other: Optional[str]
    sender: Optional[str]
    email: Optional[str]
    telephone: Optional[str]
    source: Optional[IdNameModelOut]
    organization: Optional[IdNameModelOut]
    remarks: list[RemarksModelOut]
    history: list
    related_letters: list
    department: Optional[IdNameModelOut]
    status: Optional[IdNameModelOut]
    assignee: Optional[IdNameModelOut]
    attachments: list[AttachmentModelOut]
    content: str

    @field_validator('received_datetime', 'create_datetime', mode='after')
    @classmethod
    def ensure_timezone(cls, value):
        return value.replace(tzinfo=timezone.utc)


class LetterModelOutList(BaseModel):
    id: int
    code: str
    create_datetime: datetime
    subject: Optional[str]
    department: Optional[str]
    status: Optional[str]
    assignee: Optional[str]
    organization: Optional[str]
    other: Optional[str]

    @field_validator('create_datetime', mode='after')
    @classmethod
    def ensure_timezone(cls, value):
        return value.replace(tzinfo=timezone.utc)


class SwitchAttributeType(str, Enum):
    status = "status"
    assignee = "assignee"
    department = "department"


class SwitchLetterAttribute(BaseModel):
    current_id: Optional[int]
    next_id: int


class LetterExcelFilter(BaseModel):
    limit: Optional[int] = None
    create_date_start: Optional[datetime] = None
    create_date_end: Optional[datetime] = None
    columns: Optional[list[str]] = None
