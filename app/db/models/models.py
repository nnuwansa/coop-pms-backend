import enum

from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Boolean, Text, func, Enum
)
from datetime import datetime
from sqlalchemy.orm import relationship, declarative_base

LETTER_DOT_ID = "letter.id"

Base = declarative_base()


class ActionEnum(enum.Enum):
    radio = "radio"
    check = "check"


class Letter(Base):
    __tablename__ = "letter"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(255), index=True, nullable=False)
    received_datetime = Column(DateTime, default=func.utc_timestamp())
    subject = Column(String(255), nullable=False)
    other = Column(Text)
    content = Column(Text)
    sender = Column(String(255))
    email = Column(String(255))
    telephone = Column(String(20))
    sender_subject_no = Column(String(50), nullable=True)
    registered_post_no = Column(String(50), nullable=True)  # NEW
    source_id = Column(Integer, ForeignKey("source.id"))
    organization_id = Column(Integer, ForeignKey("organization.id"))
    status_id = Column(Integer, ForeignKey("status.id"))
    create_datetime = Column(DateTime, default=func.utc_timestamp())
    update_datetime = Column(DateTime, default=func.utc_timestamp(), onupdate=func.utc_timestamp())
    is_active = Column(Boolean, default=True)
    status_since = Column(DateTime, default=func.utc_timestamp())  # NEW
    last_reminder_sent = Column(DateTime, nullable=True)  # NEW
    completion_file_name = Column(String(255), nullable=True)  # NEW
    cheque_deposited = Column(Boolean, default=False)  # NEW
    cheque_deposit_date = Column(DateTime, nullable=True)  # NEW
    cheque_account_no = Column(String(100), nullable=True)  # NEW
    cheque_bank = Column(String(150), nullable=True)  # NEW
    cheque_branch = Column(String(150), nullable=True)  # NEW
    recommended_to_id = Column(Integer, ForeignKey("system_user.id"), nullable=True)  # NEW — who this letter is recommended to, separate from assignees
    forwarded_to_id = Column(Integer, ForeignKey("system_user.id"), nullable=True)  # NEW — who this letter was forwarded to. Separate from assignees AND from recommended_to: forwarding never needs a status change, and never removes/overwrites who the letter is actually assigned to or recommended to.
    initials_by_user_id = Column(Integer, ForeignKey("system_user.id"), nullable=True)  # NEW — who this letter's reply/report was initialled by (e.g. the administration officer), for the printed seal block
    initials_by_notes = Column(Text, nullable=True)  # NEW — optional note attached to the Initials By selection
    initials_by_pending_user_id = Column(Integer, ForeignKey("system_user.id"), nullable=True)  # NEW — who admin selected, awaiting THEIR confirmation
    order_by_role_id = Column(Integer, ForeignKey("order_by_option.id"), nullable=True)
    order_by_action_id = Column(Integer, ForeignKey("order_by_option.id"), nullable=True)
    order_by_role = relationship("OrderByOption", foreign_keys=[order_by_role_id])
    order_by_action = relationship("OrderByOption", foreign_keys=[order_by_action_id])
    # Relationships
    remarks = relationship("Remark", back_populates="letter")
    history = relationship("History")
    related_letters1 = relationship("LetterRelation", foreign_keys="[LetterRelation.letter_id]")
    related_letters2 = relationship("LetterRelation", foreign_keys="[LetterRelation.related_letter_id]")
    status = relationship("Status")
    attachments = relationship("LetterAttachment")
    source = relationship("Source")
    organization = relationship("Organization")
    assignees = relationship("LetterAssignee", back_populates="letter")
    departments = relationship("LetterDepartment", back_populates="letter")
    recommended_to = relationship("SystemUser", foreign_keys=[recommended_to_id])  # NEW
    forwarded_to = relationship("SystemUser", foreign_keys=[forwarded_to_id])  # NEW
    initials_by = relationship("SystemUser", foreign_keys=[initials_by_user_id])  # NEW
    initials_by_pending = relationship("SystemUser", foreign_keys=[initials_by_pending_user_id])  # NEW
    assignee_statuses = relationship("LetterAssigneeStatus", back_populates="letter")  # NEW
    is_public_complaint = Column(Boolean, default=False)  # NEW

class LetterRelation(Base):
    __tablename__ = "letter_relation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    letter_id = Column(Integer, ForeignKey(LETTER_DOT_ID))
    related_letter_id = Column(Integer, ForeignKey(LETTER_DOT_ID))
    relation_type = Column(String(100))
    update_datetime = Column(DateTime, default=func.utc_timestamp(), onupdate=func.utc_timestamp())
    create_datetime = Column(DateTime, default=func.utc_timestamp())
    is_active = Column(Boolean, default=True)


class Remark(Base):
    __tablename__ = "remark"

    id = Column(Integer, primary_key=True, autoincrement=True)
    letter_id = Column(Integer, ForeignKey(LETTER_DOT_ID))
    content = Column(Text, nullable=False)
    subject_no = Column(String(50), nullable=True)
    created_by_id = Column(Integer, ForeignKey("system_user.id"), nullable=True)   # NEW
    created_by_name = Column(String(255), nullable=True)                          # NEW
    create_datetime = Column(DateTime, default=func.utc_timestamp())
    update_datetime = Column(DateTime, default=func.utc_timestamp(), onupdate=func.utc_timestamp())
    status = Column(String(100))
    department = Column(String(255))
    assignee = Column(String(255))
    is_active = Column(Boolean, default=True)

    # Relationship
    attachments = relationship("RemarkAttachment")
    letter = relationship("Letter", back_populates="remarks")


class RemarkHistory(Base):          # NEW TABLE — edit/delete audit trail
    __tablename__ = "remark_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    remark_id = Column(Integer, ForeignKey("remark.id"))
    letter_id = Column(Integer, ForeignKey(LETTER_DOT_ID))
    action = Column(String(20), nullable=False)          # "edit" | "delete"
    content_before = Column(Text, nullable=False)
    content_after = Column(Text, nullable=True)
    reason = Column(Text, nullable=False)
    changed_by = Column(String(255), nullable=False)
    changed_by_email = Column(String(255))
    create_datetime = Column(DateTime, default=func.utc_timestamp())


class RemarkAttachment(Base):
    __tablename__ = "remark_attachment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    remark_id = Column(Integer, ForeignKey("remark.id"))
    title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)   # NEW — bytes
    update_datetime = Column(DateTime, default=func.utc_timestamp(), onupdate=func.utc_timestamp())
    create_datetime = Column(DateTime, default=func.utc_timestamp())


class LetterAttachment(Base):
    __tablename__ = "letter_attachment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    letter_id = Column(Integer, ForeignKey("letter.id"))
    title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)   # NEW — bytes
    update_datetime = Column(DateTime, default=func.utc_timestamp(), onupdate=func.utc_timestamp())
    create_datetime = Column(DateTime, default=func.utc_timestamp())


class SystemUser(Base):
    __tablename__ = "system_user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    employee_id = Column(String(50), nullable=True, unique=True)
    nic = Column(String(20), nullable=True)
    designation_id = Column(Integer, ForeignKey("designation.id"), nullable=True)
    password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("role.id"))
    department_id = Column(Integer, ForeignKey("department.id"))
    update_datetime = Column(DateTime, default=func.utc_timestamp(), onupdate=func.utc_timestamp())
    create_datetime = Column(DateTime, default=func.utc_timestamp())
    is_active = Column(Boolean, default=False)
    is_department_account = Column(Boolean, default=False)
    department_unit_id = Column(Integer, ForeignKey("department_unit.id"), nullable=True)  # NEW
    department_unit = relationship("DepartmentUnit")  # NEW
    is_default_initials_by = Column(Boolean, default=False)  # NEW — at most one user should have this true; the Initials By picker pre-selects them by default on a fresh letter, until an admin picks someone else for that letter

    role = relationship("Role")
    department = relationship("Department")
    designation = relationship("Designation")

class Designation(Base):
    __tablename__ = "designation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    update_datetime = Column(DateTime, default=func.utc_timestamp(), onupdate=func.utc_timestamp())
    create_datetime = Column(DateTime, default=func.utc_timestamp())
    is_active = Column(Boolean, default=True)

class RefreshToken(Base):
    __tablename__ = "refresh_token"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("system_user.id"))
    token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.utc_timestamp())
    is_revoked = Column(Boolean, default=False)

class SystemUserHistory(Base):
    __tablename__ = "system_user_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    action = Column(String(50), nullable=False)
    description = Column(String(500), nullable=False)
    performed_by = Column(String(255), nullable=True)
    create_datetime = Column(DateTime, default=func.utc_timestamp())

class Source(Base):
    __tablename__ = "source"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    code = Column(String, nullable=True)
    update_datetime = Column(DateTime, default=func.utc_timestamp(), onupdate=func.utc_timestamp())
    create_datetime = Column(DateTime, default=func.utc_timestamp())
    is_active = Column(Boolean, default=True)


class Organization(Base):
    __tablename__ = "organization"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=True)
    email = Column(String(255), nullable=True)
    telephone = Column(String(20), nullable=True)
    update_datetime = Column(DateTime, default=func.utc_timestamp(), onupdate=func.utc_timestamp())
    create_datetime = Column(DateTime, default=func.utc_timestamp())
    is_active = Column(Boolean, default=True)
    fax_no = Column(String(20), nullable=True)  # NEW


class LetterAssignee(Base):
    __tablename__ = "letter_assignee"
    id = Column(Integer, primary_key=True, autoincrement=True)
    letter_id = Column(Integer, ForeignKey("letter.id"))
    assignee_id = Column(Integer, ForeignKey("system_user.id"))
    assigned_by_user_id = Column(Integer, ForeignKey("system_user.id"), nullable=True)  # NEW — who added this assignee
    create_datetime = Column(DateTime, default=func.utc_timestamp())
    letter = relationship("Letter", back_populates="assignees")
    assignee = relationship("SystemUser", foreign_keys=[assignee_id])  # <-- foreign_keys add කරන්න
    assigned_by = relationship("SystemUser", foreign_keys=[assigned_by_user_id])

class LetterDepartment(Base):
    __tablename__ = "letter_department"
    id = Column(Integer, primary_key=True, autoincrement=True)
    letter_id = Column(Integer, ForeignKey("letter.id"))
    department_id = Column(Integer, ForeignKey("department.id"))
    department_unit_id = Column(Integer, ForeignKey("department_unit.id"), nullable=True)  # ADD THIS
    create_datetime = Column(DateTime, default=func.utc_timestamp())
    letter = relationship("Letter", back_populates="departments")
    department = relationship("Department")
    department_unit = relationship("DepartmentUnit")


class LetterAssigneeStatus(Base):   # NEW
    __tablename__ = "letter_assignee_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    letter_id = Column(Integer, ForeignKey("letter.id"))
    assignee_id = Column(Integer, ForeignKey("system_user.id"))
    status_id = Column(Integer, ForeignKey("status.id"))
    file_name = Column(String(255), nullable=True)
    copies_forwarded_to = Column(Text, nullable=True)   # NEW — who copies of this assignee's response were sent to
    summary = Column(Text, nullable=True)                # NEW — short summary of the reply/action taken, recorded alongside the status change
    status_since = Column(DateTime, default=func.utc_timestamp())
    reminder_sent = Column(Boolean, default=False,nullable=False)  # NEW — prevents sending the 3-day reminder more than once per pending status
    create_datetime = Column(DateTime, default=func.utc_timestamp())
    update_datetime = Column(DateTime, default=func.utc_timestamp(), onupdate=func.utc_timestamp())

    letter = relationship("Letter", back_populates="assignee_statuses")
    assignee = relationship("SystemUser")
    status = relationship("Status")

class DepartmentUnit(Base):   # NEW
    __tablename__ = "department_unit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    department_id = Column(Integer, ForeignKey("department.id"))
    name = Column(String(255), nullable=False)
    email = Column(String(150), nullable=True)  # NEW
    is_active = Column(Boolean, default=True)
    create_datetime = Column(DateTime, default=func.utc_timestamp())
    update_datetime = Column(DateTime, default=func.utc_timestamp(), onupdate=func.utc_timestamp())

    department = relationship("Department", back_populates="units")


class RoleAssignableDepartment(Base):   # NEW
    __tablename__ = "role_assignable_department"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("role.id"))
    department_id = Column(Integer, ForeignKey("department.id"))


class RoleAssignableRole(Base):   # NEW
    __tablename__ = "role_assignable_role"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("role.id"))
    assignable_role_id = Column(Integer, ForeignKey("role.id"))
class Role(Base):
    __tablename__ = "role"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(String(255))
    update_datetime = Column(DateTime, default=func.utc_timestamp(), onupdate=func.utc_timestamp())
    create_datetime = Column(DateTime, default=func.utc_timestamp())
    is_active = Column(Boolean, default=True)

    # Relationships
    permissions = relationship("Permission", secondary="role_permission")
    allowed_statuses = relationship("RoleStatusPermission", back_populates="role")

class RolePermission(Base):
    __tablename__ = "role_permission"

    role_id = Column(Integer, ForeignKey("role.id"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permission.id"), primary_key=True)


class Permission(Base):
    __tablename__ = "permission"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    code = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    action = Column(Enum(ActionEnum), nullable=False)
    create_datetime = Column(DateTime, default=func.utc_timestamp())

class RoleStatusPermission(Base):
    __tablename__ = "role_status_permission"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("role.id"))
    status_id = Column(Integer, ForeignKey("status.id"))

    role = relationship("Role", back_populates="allowed_statuses")
    status = relationship("Status")

class Department(Base):
    __tablename__ = "department"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    update_datetime = Column(DateTime, default=func.utc_timestamp(), onupdate=func.utc_timestamp())
    create_datetime = Column(DateTime, default=func.utc_timestamp())
    is_active = Column(Boolean, default=True)
    email = Column(String(255), nullable=True)
    units = relationship("DepartmentUnit", back_populates="department")  # NEW


class EmployeeName(Base):
    __tablename__ = "employee_name"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    update_datetime = Column(DateTime, default=func.utc_timestamp(), onupdate=func.utc_timestamp())
    create_datetime = Column(DateTime, default=func.utc_timestamp())
class Status(Base):
    __tablename__ = "status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    update_datetime = Column(DateTime, default=func.utc_timestamp(), onupdate=func.utc_timestamp())
    create_datetime = Column(DateTime, default=func.utc_timestamp())
    is_active = Column(Boolean, default=True)
    requires_file_name = Column(Boolean, default=False)  # NEW
    requires_copies_forwarded_to = Column(Boolean, default=False)  # NEW — admin can require "Copies Forwarded To" when an assignee sets a letter to this status
    requires_summary = Column(Boolean, default=False)  # NEW — admin can require a short Summary when an assignee sets a letter to this status


class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String(500), nullable=False)
    username = Column(String(255))
    email = Column(String(255))
    letter_id = Column(Integer, ForeignKey(LETTER_DOT_ID))
    create_datetime = Column(DateTime, default=func.utc_timestamp())


# ─── Letter Upload Collection ──────────────────────────────────────────────
# NEW — lets someone with `letter.upload_collection` upload a letter file
# into their own personal collection (e.g. a scanned copy received outside
# the normal registration flow), without going through full letter
# creation. Admins with `letter.upload_collection_view` can browse and
# download everything uploaded by everyone.
class LetterUpload(Base):
    __tablename__ = "letter_upload"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uploaded_by_id = Column(Integer, ForeignKey("system_user.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=False)  # stored filename on disk
    file_size = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    create_datetime = Column(DateTime, default=func.utc_timestamp())

    uploaded_by = relationship("SystemUser")


# ─── File Management ────────────────────────────────────────────────────────
# NEW — file numbers pre-registered under a Section/Unit and Subject, each
# optionally assigned to a specific person. This is what backs the File
# Name picker on Assignee Status: an assignee only ever sees the files
# assigned to them, instead of typing a free-text file name from memory.
class ManagedFile(Base):
    __tablename__ = "managed_file"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_number = Column(String(100), nullable=False, unique=True)
    department_id = Column(Integer, ForeignKey("department.id"), nullable=False)
    department_unit_id = Column(Integer, ForeignKey("department_unit.id"), nullable=True)
    subject = Column(String(500), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("system_user.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    create_datetime = Column(DateTime, default=func.utc_timestamp())

    department = relationship("Department")
    department_unit = relationship("DepartmentUnit")
    assigned_to = relationship("SystemUser")


class OrderByOption(Base):
    __tablename__ = "order_by_option"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)   # e.g. "සමූපකාර සංවර්ධන කොමසාරිස්..."
    category = Column(String(20), nullable=False, default="action")  # NEW
    is_active = Column(Boolean, default=True, nullable=False)
    create_datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)   # who added it — helps tell "admin-added" vs "quick-add from letter view" apart if you ever want that distinction