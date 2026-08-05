
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from typing import Optional, List
from pydantic import BaseModel, field_validator


class LetterFilter(BaseModel):
    id: Optional[int] = None
    ids: Optional[List[int]] = None
    code: Optional[str] = None
    subject: Optional[str] = None
    department_id: Optional[int] = None
    assignee_id: Optional[int] = None
    status_id: Optional[int] = None
    organization_id: Optional[int] = None
    create_date_start: Optional[datetime] = None
    create_date_end: Optional[datetime] = None
    other: Optional[str] = None
    has_cheque: Optional[bool] = None
    pending_only: Optional[bool] = None
    pending_days_min: Optional[int] = None
    pending_days_max: Optional[int] = None
    assignee_status_id: Optional[int] = None


class LetterModelIn(BaseModel):
    code: str
    received_datetime: datetime
    subject: Optional[str] = None
    other: Optional[str] = None
    sender: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    sender_subject_no: Optional[str] = None
    registered_post_no: Optional[str] = None   # NEW
    source_id: Optional[int] = None
    organization_id: Optional[int] = None
    assignee_ids: Optional[List[int]] = []
    department_ids: Optional[List[int]] = []

    @field_validator('sender', 'email', 'telephone', 'other', 'registered_post_no', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v


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
    sender_subject_no: Optional[str] = None
    registered_post_no: Optional[str] = None   # NEW
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
    file_size: Optional[int] = None   # NEW

    @field_validator('create_datetime', mode='after')
    @classmethod
    def ensure_timezone(cls, value):
        return value.replace(tzinfo=timezone.utc)


class RemarksModelOut(BaseModel):
    id: int
    content: str
    subject_no: Optional[str] = None
    create_datetime: datetime
    department: Optional[str]
    status: Optional[str]
    assignee: Optional[str]
    created_by: Optional[str] = None   # NEW
    attachments: list[AttachmentModelOut]

    @field_validator('create_datetime', mode='after')
    @classmethod
    def ensure_timezone(cls, value):
        return value.replace(tzinfo=timezone.utc)


class RemarkUpdateIn(BaseModel):          # NEW
    content: str
    subject_no: Optional[str] = None
    reason: str

    @field_validator('reason')
    @classmethod
    def reason_required(cls, v):
        if not v or not v.strip():
            raise ValueError("Reason for change is required")
        return v.strip()


class RemarkDeleteIn(BaseModel):          # NEW
    reason: str

    @field_validator('reason')
    @classmethod
    def reason_required(cls, v):
        if not v or not v.strip():
            raise ValueError("Reason for change is required")
        return v.strip()


class RemarkHistoryModelOut(BaseModel):   # NEW
    id: int
    remark_id: int
    action: str
    content_before: str
    content_after: Optional[str] = None
    reason: str
    changed_by: str
    changed_by_email: Optional[str] = None
    create_datetime: datetime

    @field_validator('create_datetime', mode='after')
    @classmethod
    def ensure_timezone(cls, value):
        return value.replace(tzinfo=timezone.utc)

    class Config:
        from_attributes = True


class IdNameModelOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
class LetterAssigneeStatusIn(BaseModel):   # NEW
    status_id: int
    file_name: Optional[str] = None


class LetterAssigneeStatusOut(BaseModel):   # NEW
    assignee_id: int
    assignee_name: str
    status_id: int
    status_name: str
    file_name: Optional[str] = None
    status_since: Optional[datetime] = None
    status_days: Optional[int] = None
    can_edit: bool = False   # true only for the logged-in assignee's own row

    @field_validator('status_since', mode='after')
    @classmethod
    def ensure_timezone(cls, value):
        if value is None:
            return value
        return value.replace(tzinfo=timezone.utc)

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
    sender_subject_no: Optional[str] = None
    registered_post_no: Optional[str] = None   # NEW
    source: Optional[IdNameModelOut]
    organization: Optional[IdNameModelOut]
    remarks: list[RemarksModelOut]
    history: list
    related_letters: list
    status: Optional[IdNameModelOut]
    status_id: Optional[int] = None
    attachments: list[AttachmentModelOut]
    content: Optional[str] = None
    departments: list[IdNameModelOut] = []
    assignees: list[IdNameModelOut] = []
    recommended_to: Optional[IdNameModelOut] = None  # NEW — separate from assignees; who this letter was recommended to, distinct from who it's assigned to
    forwarded_to: Optional[IdNameModelOut] = None  # NEW — separate from assignees and recommended_to; who this letter was forwarded to, with no status attached
    status_since: Optional[datetime] = None  # NEW
    status_days: Optional[int] = None  # NEW
    completion_file_name: Optional[str] = None  # NEW
    cheque_deposited: bool = False
    cheque_deposit_date: Optional[datetime] = None
    cheque_account_no: Optional[str] = None
    cheque_bank: Optional[str] = None
    cheque_branch: Optional[str] = None
    assignee_statuses: List[LetterAssigneeStatusOut] = []
    remarks_count: int = 0  # NEW — total active remark count, so the Remarks tab can show a badge without needing to switch tabs first

    @field_validator('received_datetime', 'create_datetime', 'status_since', mode='after')
    @classmethod
    def ensure_timezone(cls, value):
        if value is None:
            return value
        return value.replace(tzinfo=timezone.utc)


class AssigneeStatusBrief(BaseModel):   # NEW — structured per-assignee status for the dashboard table
    assignee_name: str
    status_name: str
    file_name: Optional[str] = None


class LetterModelOutList(BaseModel):
    id: int
    code: str
    create_datetime: datetime
    subject: Optional[str]
    department: Optional[str]
    department_account_ids: List[int] = []  # NEW
    status: Optional[str]
    assignee: Optional[str]
    assignee_ids: List[int] = []  # NEW — actual assignee ids, needed so the Quick Edit dialog can preselect who's already assigned (the `assignee` field above is only a display string of names, not usable for checkboxes)
    organization: Optional[str]
    other: Optional[str]
    sender_subject_no: Optional[str] = None
    status_since: Optional[datetime] = None  # NEW
    status_days: Optional[int] = None  # NEW
    completion_file_name: Optional[str] = None  # NEW — File Name, shown/exported when a status required and saved one
    forwarded_to: Optional[str] = None  # NEW — who this letter was forwarded to, for quick visibility on the list/dashboard
    cheque_deposited: bool = False  # NEW
    cheque_deposit_date: Optional[datetime] = None  # NEW
    cheque_account_no: Optional[str] = None  # NEW
    cheque_bank: Optional[str] = None  # NEW
    cheque_branch: Optional[str] = None  # NEW
    days_pending: Optional[int] = None  # NEW — days since received_datetime; freezes once ALL assignees are "Completed" (or, for letters with no assignees, once the letter's own status is "Completed")
    # CHANGED — was List[str] of "Name: Status" text. Now structured objects
    # so the frontend can color-code each badge by its own status_name
    # instead of everything rendering in one flat purple color, and so the
    # per-assignee file_name (set when a status like "Completed" required
    # one) can be shown next to that assignee's name in the File Name
    # column, instead of relying on the old single overall `completion_file_name`
    # field which per-assignee statuses never populate.
    assignee_statuses: List[AssigneeStatusBrief] = []
    remarks_count: int = 0  # NEW — total active remark count, for a notify badge in the dashboard's Actions column

    @field_validator('create_datetime', mode='after')
    @classmethod
    def ensure_timezone(cls, value):
        return value.replace(tzinfo=timezone.utc)

    @field_validator('cheque_deposit_date', mode='after')
    @classmethod
    def ensure_timezone_cheque(cls, value):
        if value is None:
            return value
        return value.replace(tzinfo=timezone.utc)


class SwitchAttributeType(str, Enum):
    status = "status"
    assignee = "assignee"
    department = "department"


class SwitchLetterAttribute(BaseModel):
    current_id: Optional[int]
    next_id: int


class LetterExcelFilter(BaseModel):
    ids: Optional[List[int]] = None  # NEW — explicit list of letter IDs (e.g. from a table's row-selection checkboxes). When set, this takes priority over limit/create_date_start/create_date_end in letters_excel_data — those are ignored rather than combined with it.
    limit: Optional[int] = None
    create_date_start: Optional[datetime] = None
    create_date_end: Optional[datetime] = None
    columns: Optional[list[str]] = None


class LetterAssignmentIn(BaseModel):
    status_id: Optional[int] = None
    department_ids: Optional[List[int]] = []
    assignee_ids: List[int] = []
    file_name: Optional[str] = None  # NEW
    recommended_to_id: Optional[int] = None  # NEW — who a "Recommendation" status letter is recommended to; kept separate from assignee_ids so it never overwrites the actual assignee list
    forwarded_to_id: Optional[int] = None  # NEW — who this letter is forwarded to; independent of status, assignees, and recommended_to


class ChequeDepositIn(BaseModel):   # NEW
    deposited: bool
    deposit_date: Optional[datetime] = None
    account_no: Optional[str] = None
    bank: Optional[str] = None
    branch: Optional[str] = None

    class LetterAssigneeStatusIn(BaseModel):  # NEW
        status_id: int
        file_name: Optional[str] = None

    class LetterAssigneeStatusOut(BaseModel):  # NEW
        assignee_id: int
        assignee_name: str
        status_id: int
        status_name: str
        file_name: Optional[str] = None
        status_since: Optional[datetime] = None
        status_days: Optional[int] = None
        can_edit: bool = False  # true only for the logged-in assignee's own row

        @field_validator('status_since', mode='after')
        @classmethod
        def ensure_timezone(cls, value):
            if value is None:
                return value
            return value.replace(tzinfo=timezone.utc)