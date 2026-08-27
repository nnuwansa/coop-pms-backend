from logging import getLogger
from typing import Optional

from sqlalchemy.orm import Session

from db.models.models import ManagedFile
from exception.exception import DuplicateEntryException

logger = getLogger(__name__)


async def file_number_exists(file_number: str, db: Session, exclude_id: Optional[int] = None) -> bool:
    query = db.query(ManagedFile).filter(ManagedFile.file_number == file_number, ManagedFile.is_active)
    if exclude_id:
        query = query.filter(ManagedFile.id != exclude_id)
    return db.query(query.exists()).scalar()


async def save_managed_file(managed_file: ManagedFile, db: Session) -> ManagedFile:
    db.add(managed_file)
    db.commit()
    db.refresh(managed_file)
    return managed_file


async def get_managed_file_by_id(file_id: int, db: Session):
    return db.query(ManagedFile).filter(
        ManagedFile.id == file_id, ManagedFile.is_active
    ).first()


async def get_managed_files(
        db: Session,
        department_id: Optional[int] = None,
        department_unit_id: Optional[int] = None,
        assigned_to_id: Optional[int] = None,
):
    query = db.query(ManagedFile).filter(ManagedFile.is_active)
    if department_id:
        query = query.filter(ManagedFile.department_id == department_id)
    if department_unit_id:
        query = query.filter(ManagedFile.department_unit_id == department_unit_id)
    if assigned_to_id:
        query = query.filter(ManagedFile.assigned_to_id == assigned_to_id)
    return query.order_by(ManagedFile.file_number).all()


async def get_managed_files_by_assignee(user_id: int, db: Session):
    return (
        db.query(ManagedFile)
        .filter(ManagedFile.assigned_to_id == user_id, ManagedFile.is_active)
        .order_by(ManagedFile.file_number)
        .all()
    )


async def update_managed_file(managed_file: ManagedFile, db: Session) -> ManagedFile:
    db.commit()
    db.refresh(managed_file)
    return managed_file


async def soft_delete_managed_file(managed_file: ManagedFile, db: Session) -> ManagedFile:
    managed_file.is_active = False
    db.commit()
    db.refresh(managed_file)
    return managed_file