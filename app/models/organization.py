# from datetime import datetime
#
# from pydantic import BaseModel
#
#
# class OrganizationModelIn(BaseModel):
#     name: str
#
#
# class OrganizationModelOut(BaseModel):
#     id: int
#     name: str
#     create_datetime: datetime
#     update_datetime: datetime
#
#     class Config:
#         from_attributes = True



from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class OrganizationModelIn(BaseModel):
    name: str
    address: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None

class OrganizationModelOut(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    create_datetime: datetime
    update_datetime: datetime

    class Config:
        from_attributes = True