from typing import Optional, List

from pydantic import BaseModel


class RoleModelIn(BaseModel):
    name: str
    description: Optional[str] = None


class RoleModelOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permission_count: Optional[int] = None

    class Config:
        from_attributes = True


class RolePermissionUpdateRequest(BaseModel):
    permission_ids: List[int]
    status_ids: List[int] = []

class RolePermissionsOut(BaseModel):   # NEW — replaces the old bare List[int] response
    permission_ids: List[int]
    status_ids: List[int]

class AssignableUserOut(BaseModel):
    """A registered user, shown in the role dialogs' user picker."""
    id: int
    name: str
    current_role_id: Optional[int] = None
    current_role_name: Optional[str] = None


class RoleUserAssignRequest(BaseModel):
    user_ids: List[int]