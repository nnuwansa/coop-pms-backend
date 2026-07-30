
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator


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
    department_unit_id: Optional[int] = None  # NEW


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
    department_unit_id: Optional[int] = None  # NEW


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
    department_unit_id: Optional[int] = None  # NEW
    is_department_account: bool = False  # NEW
    role: Optional[str] = None
    permissions: list[str] = []
    allowed_status_ids: list[int] = []
    allowed_department_ids: list[int] = []
    allowed_assignee_role_ids: list[int] = []

    class Config:
        from_attributes = True


class SystemUserModelNamesOut(BaseModel):
    id: int
    name: str
    department_id: Optional[int] = None
    department_unit_id: Optional[int] = None


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
    department_unit: Optional[str] = None


class SystemUserHistoryOut(BaseModel):
    id: int
    action: str
    description: str
    performed_by: Optional[str] = None
    create_datetime: datetime

    class Config:
        from_attributes = True


class DepartmentAccountIn(BaseModel):
    # CHANGED — now supports creating a login for EITHER a Section OR a
    # Sub-Unit. Exactly one of `department_id` / `department_unit_id`
    # must be provided; the validator below enforces that.
    department_id: Optional[int] = None
    department_unit_id: Optional[int] = None  # NEW
    email: str
    password: str

    @model_validator(mode="after")
    def check_exactly_one_target(self):
        if not self.department_id and not self.department_unit_id:
            raise ValueError("Either department_id or department_unit_id must be provided")
        if self.department_id and self.department_unit_id:
            raise ValueError("Provide only one of department_id or department_unit_id, not both")
        return self