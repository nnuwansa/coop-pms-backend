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
