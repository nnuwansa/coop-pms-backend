# from typing import List
#
# from pydantic import BaseModel
#
#
# class PermissionModelIn(BaseModel):
#     name: str
#     code: str
#     description: str
#
#
# class PermissionModel(BaseModel):
#     id: int
#     name: str
#     code: str
#     description: str
#
#
# class PermissionModelOut(BaseModel):
#     category: str
#     action: str
#     permissions: List[PermissionModel]

from typing import List, Literal

from pydantic import BaseModel


class PermissionModelIn(BaseModel):
    name: str
    code: str
    description: str
    # CHANGED — the Permission table has `category` (free-text grouping
    # label, e.g. "Letter Management") and `action` (NOT NULL columns).
    # create_permission() previously never set these, which is exactly
    # what was causing every "Add Permission" request to fail with a DB
    # error (NOT NULL constraint violation surfaced as a 400).
    category: str
    action: Literal["radio", "check"] = "check"


class PermissionModel(BaseModel):
    id: int
    name: str
    code: str
    description: str


class PermissionModelOut(BaseModel):
    category: str
    action: str
    permissions: List[PermissionModel]