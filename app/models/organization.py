from datetime import datetime

from pydantic import BaseModel


class OrganizationModelIn(BaseModel):
    name: str


class OrganizationModelOut(BaseModel):
    id: int
    name: str
    create_datetime: datetime
    update_datetime: datetime

    class Config:
        from_attributes = True
