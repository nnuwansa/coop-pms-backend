from logging import getLogger
from typing import Optional

from sqlalchemy.orm import Session

from crud.managed_file import (
    file_number_exists, save_managed_file, get_managed_file_by_id, get_managed_files,
    get_managed_files_by_assignee, update_managed_file, soft_delete_managed_file,
)
from db.models.models import ManagedFile
from exception.exception import NoDataFoundException, DuplicateEntryException
from models.managed_file import ManagedFileIn, ManagedFileOut, ManagedFileBrief

logger = getLogger(__name__)


def _to_out(managed_file: ManagedFile) -> ManagedFileOut:
    return ManagedFileOut(
        id=managed_file.id,
        file_number=managed_file.file_number,
        department_id=managed_file.department_id,
        department_name=managed_file.department.name if managed_file.department else "",
        department_unit_id=managed_file.department_unit_id,
        department_unit_name=managed_file.department_unit.name if managed_file.department_unit else None,
        subject=managed_file.subject,
        assigned_to_id=managed_file.assigned_to_id,
        assigned_to_name=(
            f"{managed_file.assigned_to.first_name} {managed_file.assigned_to.last_name}"
            if managed_file.assigned_to else None
        ),
        create_datetime=managed_file.create_datetime,
    )


async def create_managed_file_service(payload: ManagedFileIn, db: Session, current_user):
    logger.info("Create managed file process started")

    if await file_number_exists(payload.file_number, db):
        raise DuplicateEntryException(f"File number '{payload.file_number}' already exists")

    managed_file = ManagedFile(
        file_number=payload.file_number,
        department_id=payload.department_id,
        department_unit_id=payload.department_unit_id,
        subject=payload.subject,
        assigned_to_id=payload.assigned_to_id or current_user.id,  # blank → the person adding it
        created_by_id = current_user.id,
    )
    managed_file_db = await save_managed_file(managed_file, db)

    logger.info("Create managed file process ended")
    return _to_out(managed_file_db)


async def list_managed_files_service(
        db: Session,
        current_user,
        department_id: Optional[int] = None,
        department_unit_id: Optional[int] = None,
        assigned_to_id: Optional[int] = None,
):
    visible_to = None if _sees_all(current_user) else current_user.id
    files = await get_managed_files(db, department_id, department_unit_id, assigned_to_id,visible_to_user_id = visible_to)
    return [_to_out(f) for f in files]


async def list_my_managed_files_service(user_id: int, db: Session):
    files = await get_managed_files_by_assignee(user_id, db)
    return [ManagedFileBrief(id=f.id, file_number=f.file_number, subject=f.subject) for f in files]


async def update_managed_file_service(file_id: int, payload: ManagedFileIn, db: Session, current_user):
    logger.info(f"Update managed file process started for ID {file_id}")

    managed_file = await _get_accessible_file(file_id, current_user, db)

    if not managed_file:
        raise NoDataFoundException(f"File with ID {file_id} not found")

    if await file_number_exists(payload.file_number, db, exclude_id=file_id):
        raise DuplicateEntryException(f"File number '{payload.file_number}' already exists")

    managed_file.file_number = payload.file_number
    managed_file.department_id = payload.department_id
    managed_file.department_unit_id = payload.department_unit_id
    managed_file.subject = payload.subject
    if payload.assigned_to_id:  # blank keeps the current owner
        managed_file.assigned_to_id = payload.assigned_to_id

    updated = await update_managed_file(managed_file, db)

    logger.info(f"Update managed file process ended for ID {file_id}")
    return _to_out(updated)


async def delete_managed_file_service(file_id: int, db: Session, current_user):
    logger.info(f"Delete managed file process started for ID {file_id}")

    managed_file = await _get_accessible_file(file_id, current_user, db)
    if not managed_file:
        raise NoDataFoundException(f"File with ID {file_id} not found")

    await soft_delete_managed_file(managed_file, db)

    logger.info(f"Delete managed file process ended for ID {file_id}")


def _sees_all(user) -> bool:
    return 'file.view_all' in user.permissions


def _owns(managed_file, user) -> bool:
    return user.id in (managed_file.assigned_to_id, managed_file.created_by_id)


async def _get_accessible_file(file_id: int, user, db: Session):
    managed_file = await get_managed_file_by_id(file_id, db)
    # NoDataFound, not Unauthorized: a 401 would make the frontend think the session expired
    if not managed_file or not (_sees_all(user) or _owns(managed_file, user)):
        raise NoDataFoundException(f"File with ID {file_id} not found")
    return managed_file
