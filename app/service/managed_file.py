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


async def create_managed_file_service(payload: ManagedFileIn, db: Session):
    logger.info("Create managed file process started")

    if await file_number_exists(payload.file_number, db):
        raise DuplicateEntryException(f"File number '{payload.file_number}' already exists")

    managed_file = ManagedFile(
        file_number=payload.file_number,
        department_id=payload.department_id,
        department_unit_id=payload.department_unit_id,
        subject=payload.subject,
        assigned_to_id=payload.assigned_to_id,
    )
    managed_file_db = await save_managed_file(managed_file, db)

    logger.info("Create managed file process ended")
    return _to_out(managed_file_db)


async def list_managed_files_service(
        db: Session,
        department_id: Optional[int] = None,
        department_unit_id: Optional[int] = None,
        assigned_to_id: Optional[int] = None,
):
    files = await get_managed_files(db, department_id, department_unit_id, assigned_to_id)
    return [_to_out(f) for f in files]


async def list_my_managed_files_service(user_id: int, db: Session):
    files = await get_managed_files_by_assignee(user_id, db)
    return [ManagedFileBrief(id=f.id, file_number=f.file_number, subject=f.subject) for f in files]


async def update_managed_file_service(file_id: int, payload: ManagedFileIn, db: Session):
    logger.info(f"Update managed file process started for ID {file_id}")

    managed_file = await get_managed_file_by_id(file_id, db)
    if not managed_file:
        raise NoDataFoundException(f"File with ID {file_id} not found")

    if await file_number_exists(payload.file_number, db, exclude_id=file_id):
        raise DuplicateEntryException(f"File number '{payload.file_number}' already exists")

    managed_file.file_number = payload.file_number
    managed_file.department_id = payload.department_id
    managed_file.department_unit_id = payload.department_unit_id
    managed_file.subject = payload.subject
    managed_file.assigned_to_id = payload.assigned_to_id

    updated = await update_managed_file(managed_file, db)

    logger.info(f"Update managed file process ended for ID {file_id}")
    return _to_out(updated)


async def delete_managed_file_service(file_id: int, db: Session):
    logger.info(f"Delete managed file process started for ID {file_id}")

    managed_file = await get_managed_file_by_id(file_id, db)
    if not managed_file:
        raise NoDataFoundException(f"File with ID {file_id} not found")

    await soft_delete_managed_file(managed_file, db)

    logger.info(f"Delete managed file process ended for ID {file_id}")