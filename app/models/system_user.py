
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SystemUserModelIn(BaseModel):
    email: str
    first_name: str
    last_name: str
    employee_id: Optional[str] = None
    nic: Optional[str] = None
    designation_id: Optional[int] = None
    password: str
    department_id: Optional[int] = None
    role_id: Optional[int] = None


class SystemUserModelUpdate(BaseModel):
    email: str
    first_name: str
    last_name: Optional[str]
    employee_id: Optional[str] = None
    nic: Optional[str] = None
    designation_id: Optional[int] = None
    password: Optional[str] = None
    department_id: Optional[int] = None
    role_id: Optional[int] = None
    is_active: Optional[bool]


class SystemUserModelOut(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    employee_id: Optional[str] = None
    nic: Optional[str] = None
    designation_id: Optional[int] = None
    department_id: Optional[int] = None
    role_id: Optional[int] = None
    update_datetime: datetime
    create_datetime: datetime

    class Config:
        from_attributes = True


class SystemUserWithPermissionsModelOut(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    department: Optional[str] = None
    department_id: Optional[int] = None
    role: Optional[str] = None
    permissions: list[str] = []

    class Config:
        from_attributes = True


class SystemUserModelNamesOut(BaseModel):
    id: int
    name: str


class SystemUserFilter(BaseModel):
    id: Optional[int] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department_id: Optional[int] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None


class SystemUserModelOutList(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: Optional[str]
    employee_id: Optional[str] = None
    nic: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class SystemUserHistoryOut(BaseModel):
    id: int
    action: str
    description: str
    performed_by: Optional[str] = None
    create_datetime: datetime

    class Config:
        from_attributes = True