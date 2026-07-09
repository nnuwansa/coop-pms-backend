import os
from logging import getLogger
from typing import List

from fastapi import UploadFile
from sqlalchemy.orm import Session

from config.config import ATTACHMENTS_DIR
from crud.letter import get_active_letter
from crud.remark import (
    create_remark, get_active_remark, update_remark_db,
    create_remark_history, get_remark_history_by_letter,
)
from db.models.models import Remark, RemarkAttachment, RemarkHistory
from exception.exception import LetterNotFoundException, NoDataFoundException, ValidationException
from models.system_user import SystemUserWithPermissionsModelOut
from utils.files import validate_files, save_attachment, delete_file

logger = getLogger(__name__)


async def create_remarks_and_attachments(
        letter_id: int,
        attachments: List[UploadFile],
        content: str,
        db: Session,
        current_user: SystemUserWithPermissionsModelOut,
        subject_no: str = None,
):
    logger.info("Create remarks process started")

    letter = await get_active_letter(letter_id, db)
    if not letter:
        raise LetterNotFoundException(f"Letter not found for ID: {letter_id}")

    await validate_files(attachments)

    remark = Remark(
        letter_id=letter_id,
        content=content,
        subject_no=subject_no,
        status=letter.status.name if letter.status else None,
        department=", ".join([ld.department.name for ld in letter.departments]) if letter.departments else None,
        assignee=", ".join([f"{la.assignee.first_name} {la.assignee.last_name}" for la in
                            letter.assignees]) if letter.assignees else None,
        created_by_id=current_user.id,
        created_by_name=f"{current_user.first_name} {current_user.last_name}",
    )
    remark = await create_remark(remark, db)
    folder_path = os.path.join(ATTACHMENTS_DIR, f"letter_{letter_id}", f"remark_{remark.id}")

    for file in attachments:
        saved_file_name, size = save_attachment(file, folder_path)
        db.add(RemarkAttachment(
            remark_id=remark.id,
            title=file.filename,
            file_name=saved_file_name,
            file_size=size,
        ))

    db.commit()
    logger.info("Create remarks process end")
    return remark.id


async def update_remark_and_attachments(
        remark_id: int,
        content: str,
        reason: str,
        db: Session,
        current_user: SystemUserWithPermissionsModelOut,
        attachments: List[UploadFile] = None,
        subject_no: str = None,
):
    logger.info(f"Update remark process started for remark_id={remark_id}")

    if not reason or not reason.strip():
        raise ValidationException("A reason for change is required to edit a remark")

    remark = await get_active_remark(remark_id, db)
    if not remark:
        raise NoDataFoundException(f"Remark with ID {remark_id} not found")

    letter = remark.letter
    if not letter:
        raise LetterNotFoundException(f"Letter not found for remark ID: {remark_id}")

    # Snapshot BEFORE overwrite — this is what powers the Remark Log history
    await create_remark_history(RemarkHistory(
        remark_id=remark.id,
        letter_id=remark.letter_id,
        action="edit",
        content_before=remark.content,
        content_after=content,
        reason=reason.strip(),
        changed_by=f"{current_user.first_name} {current_user.last_name}",
        changed_by_email=current_user.email,
    ), db)

    attachments = attachments or []
    await validate_files(attachments)

    if attachments:
        folder_path = os.path.join(ATTACHMENTS_DIR, f"letter_{letter.id}", f"remark_{remark_id}")
        for old_attachment in remark.attachments:
            db.delete(old_attachment)
            delete_file(folder_path, old_attachment.file_name)

        for file in attachments:
            saved_file_name, size = save_attachment(file, folder_path)
            db.add(RemarkAttachment(
                remark_id=remark.id,
                title=file.filename,
                file_name=saved_file_name,
                file_size=size,
            ))

    remark.content = content
    remark.subject_no = subject_no
    remark.status = letter.status.name if letter.status else None
    remark.department = ", ".join([ld.department.name for ld in letter.departments]) if letter.departments else None
    remark.assignee = ", ".join([f"{la.assignee.first_name} {la.assignee.last_name}" for la in
                                 letter.assignees]) if letter.assignees else None

    db.commit()
    logger.info(f"Update remark process completed for remark_id={remark_id}")


async def bind_remark_attachments(letter_id: int, remark_id: int, attachments: List[UploadFile], db: Session) -> List[str]:
    logger.info("Binding remark attachment process started")

    remark = await get_active_remark(remark_id, db)
    if not remark:
        raise NoDataFoundException(f"Remark with ID {remark_id} not found")

    await validate_files(attachments)

    filenames = []
    folder_path = os.path.join(ATTACHMENTS_DIR, f"letter_{letter_id}", f"remark_{remark_id}")
    for file in attachments:
        saved_file_name, size = save_attachment(file, folder_path)
        db.add(RemarkAttachment(
            remark_id=remark_id,
            title=file.filename,
            file_name=saved_file_name,
            file_size=size,
        ))
        filenames.append(file.filename)

    db.commit()
    logger.info("Binding remark attachment process end")
    return filenames


async def delete_remark_by_id(remark_id: int, reason: str, db: Session, current_user: SystemUserWithPermissionsModelOut) -> int:
    logger.info("Delete remark process started")

    if not reason or not reason.strip():
        raise ValidationException("A reason for change is required to delete a remark")

    remark_db = await get_active_remark(remark_id, db)
    if not remark_db:
        raise NoDataFoundException(f"Remark with ID {remark_id} not found")

    # Snapshot BEFORE deactivating — powers the Remark Log history
    await create_remark_history(RemarkHistory(
        remark_id=remark_db.id,
        letter_id=remark_db.letter_id,
        action="delete",
        content_before=remark_db.content,
        content_after=None,
        reason=reason.strip(),
        changed_by=f"{current_user.first_name} {current_user.last_name}",
        changed_by_email=current_user.email,
    ), db)

    remark_db.is_active = False
    saved_remark = await update_remark_db(remark_db, db)
    db.commit()

    logger.info("Delete remark process ended")
    return saved_remark.id


async def get_remark_history(letter_id: int, db: Session):
    return await get_remark_history_by_letter(letter_id, db)