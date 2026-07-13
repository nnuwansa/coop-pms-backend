
import enum

from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Boolean, Text, func, Enum
)
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


class LetterAssignee(Base):
    __tablename__ = "letter_assignee"
    id = Column(Integer, primary_key=True, autoincrement=True)
    letter_id = Column(Integer, ForeignKey("letter.id"))
    assignee_id = Column(Integer, ForeignKey("system_user.id"))
    create_datetime = Column(DateTime, default=func.utc_timestamp())
    letter = relationship("Letter", back_populates="assignees")
    assignee = relationship("SystemUser")


class LetterDepartment(Base):
    __tablename__ = "letter_department"
    id = Column(Integer, primary_key=True, autoincrement=True)
    letter_id = Column(Integer, ForeignKey("letter.id"))
    department_id = Column(Integer, ForeignKey("department.id"))
    create_datetime = Column(DateTime, default=func.utc_timestamp())
    letter = relationship("Letter", back_populates="departments")
    department = relationship("Department")


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


class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String(500), nullable=False)
    username = Column(String(255))
    email = Column(String(255))
    letter_id = Column(Integer, ForeignKey(LETTER_DOT_ID))
    create_datetime = Column(DateTime, default=func.utc_timestamp())