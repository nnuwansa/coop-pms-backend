# from datetime import datetime
#
# from pydantic import BaseModel
#
#
# class StatusModelIn(BaseModel):
#     name: str
#     requires_file_name: bool = False  # NEW
#
#
# class StatusModelOut(StatusModelIn):
#     id: int
#     name: str
#     requires_file_name: bool = False  # NEW
#     create_datetime: datetime
#     update_datetime: datetime
#
#     class Config:
#         from_attributes = True



from datetime import datetime

from pydantic import BaseModel


class StatusModelIn(BaseModel):
    name: str
    requires_file_name: bool = False  # NEW
    requires_copies_forwarded_to: bool = False  # NEW — admin toggle: require "Copies Forwarded To" when an assignee sets a letter to this status
    requires_summary: bool = False  # NEW — admin toggle: require a short Summary when an assignee sets a letter to this status


class StatusModelOut(StatusModelIn):
    id: int
    name: str
    requires_file_name: bool = False  # NEW
    requires_copies_forwarded_to: bool = False  # NEW
    requires_summary: bool = False  # NEW
    create_datetime: datetime
    update_datetime: datetime

    class Config:
        from_attributes = True