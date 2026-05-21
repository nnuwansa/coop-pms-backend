from typing import List

from pydantic import BaseModel


class PermissionModelIn(BaseModel):
    name: str
    code: str
    description: str


class PermissionModel(BaseModel):
    id: int
    name: str
    code: str
    description: str


class PermissionModelOut(BaseModel):
    category: str
    action: str
    permissions: List[PermissionModel]
