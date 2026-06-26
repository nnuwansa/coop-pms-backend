import os
from logging import getLogger
from typing import List

from fastapi import UploadFile
from sqlalchemy.orm import Session

from config.config import ATTACHMENTS_DIR
from crud.letter import get_active_letter
from crud.remark import create_remark, get_active_remark, update_remark_db
from db.models.models import Remark, RemarkAttachment
from exception.exception import LetterNotFoundException, NoDataFoundException
from utils.files import validate_files, save_attachment, delete_file

logger = getLogger(__name__)


async def create_remarks_and_attachments(letter_id: int, attachments: List[UploadFile], content: str, db: Session):
    logger.info("Create remarks process started")

    letter = await get_active_letter(letter_id, db)
    if not letter:
        raise LetterNotFoundException(f"Letter not found for ID: {letter_id}")

    await validate_files(attachments)

    # remark = Remark(
    #     letter_id=letter_id,
    #     content=content,
    #     status=letter.status.name if letter.status else None,
    #     department=letter.department.name if letter.department else None,
    #     assignee=letter.assignee.email if letter.assignee else None,
    # )
    remark = Remark(
        letter_id=letter_id,
        content=content,
        status=letter.status.name if letter.status else None,
        department=", ".join([ld.department.name for ld in letter.departments]) if letter.departments else None,
        assignee=", ".join([f"{la.assignee.first_name} {la.assignee.last_name}" for la in
                            letter.assignees]) if letter.assignees else None,
    )
    remark = await create_remark(remark, db)
    folder_path = os.path.join(ATTACHMENTS_DIR, f"letter_{letter_id}", f"remark_{remark.id}")

    for file in attachments:
        saved_file_name = save_attachment(file, folder_path)
        attachment = RemarkAttachment(
            remark_id=remark.id,
            title=file.filename,
            file_name=saved_file_name
        )
        db.add(attachment)

    db.commit()

    logger.info("Create remarks process end")
    return remark.id


async def update_remark_and_attachments(
        remark_id: int,
        content: str,
        attachments: List[UploadFile],
        db: Session
):
    logger.info(f"Update remark process started for remark_id={remark_id}")

    remark = await get_active_remark(remark_id, db)
    if not remark:
        raise NoDataFoundException(f"Remark with ID {remark_id} not found")

    letter = remark.letter
    if not letter:
        raise LetterNotFoundException(f"Letter not found in remark ID: {remark_id}")

    await validate_files(attachments)

    folder_path = os.path.join(ATTACHMENTS_DIR, f"letter_{letter.id}", f"remark_{remark_id}")
    for old_attachment in remark.attachments:
        db.delete(old_attachment)
        delete_file(folder_path, old_attachment.file_name)

    remark.content = content
    remark.status = letter.status.name if letter.status else None
    remark.department = letter.department.name if letter.department else None
    remark.assignee = letter.assignee.email if letter.assignee else None

    for file in attachments:
        saved_file_name = save_attachment(file, folder_path)
        db.add(RemarkAttachment(
            remark_id=remark.id,
            title=file.filename,
            file_name=saved_file_name
        ))

    db.commit()
    logger.info(f"Update remark process completed for remark_id={remark_id}")


async def delete_remark_by_id(remark_id: int, db: Session) -> int:
    logger.info("Delete remark process started")

    remark_db = await get_active_remark(remark_id, db)
    if not remark_db:
        raise NoDataFoundException(f"Remark with ID {remark_id} not found")

    remark_db.is_active = False
    saved_remark = await update_remark_db(remark_db, db)

    logger.info("Delete remark process ended")
    return saved_remark.id
