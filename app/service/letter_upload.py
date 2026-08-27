from typing import Optional

import os
from logging import getLogger

from fastapi import UploadFile
from sqlalchemy.orm import Session

from config.config import ATTACHMENTS_URL, ATTACHMENTS_DIR
from crud.letter_upload import (
    save_upload, get_uploads_by_user, get_all_uploads, get_upload_by_id, soft_delete_upload,
)
from db.models.models import LetterUpload
from exception.exception import NoDataFoundException, UnauthorizedException
from models.letter_upload import LetterUploadOut
from models.system_user import SystemUserWithPermissionsModelOut
from utils.files import validate_files, save_attachment, delete_file

logger = getLogger(__name__)

UPLOAD_SUBFOLDER = "upload_collection"


def _to_out(upload: LetterUpload) -> LetterUploadOut:
    return LetterUploadOut(
        id=upload.id,
        title=upload.title,
        description=upload.description,
        file_size=upload.file_size,
        url=f"{ATTACHMENTS_URL}/{UPLOAD_SUBFOLDER}/{upload.file_name}",
        uploaded_by=f"{upload.uploaded_by.first_name} {upload.uploaded_by.last_name}" if upload.uploaded_by else "Unknown",
        uploaded_by_id=upload.uploaded_by_id,
        create_datetime=upload.create_datetime,
    )


async def create_upload_service(
        title: str, description: Optional[str], file: UploadFile,
        current_user: SystemUserWithPermissionsModelOut, db: Session,
):
    logger.info("Letter upload process started")

    await validate_files([file])
    folder_path = os.path.join(ATTACHMENTS_DIR, UPLOAD_SUBFOLDER)
    saved_name, size = save_attachment(file, folder_path)

    upload = LetterUpload(
        uploaded_by_id=current_user.id,
        title=title,
        description=description,
        file_name=saved_name,
        file_size=size,
    )
    upload_db = await save_upload(upload, db)

    logger.info("Letter upload process ended")
    return _to_out(upload_db)


async def list_my_uploads_service(current_user: SystemUserWithPermissionsModelOut, db: Session):
    uploads = await get_uploads_by_user(current_user.id, db)
    return [_to_out(u) for u in uploads]


async def list_all_uploads_service(db: Session):
    uploads = await get_all_uploads(db)
    return [_to_out(u) for u in uploads]


async def delete_upload_service(upload_id: int, current_user: SystemUserWithPermissionsModelOut, db: Session):
    logger.info(f"Delete letter upload {upload_id} process started")

    upload = await get_upload_by_id(upload_id, db)
    if not upload:
        raise NoDataFoundException(f"Upload with ID {upload_id} not found")

    # NEW — a person can always delete their own upload; deleting someone
    # else's requires the admin view permission (they can see it, so they
    # can also remove it if it shouldn't be there).
    is_owner = upload.uploaded_by_id == current_user.id
    is_admin_viewer = "letter.upload_collection_view" in current_user.permissions
    if not is_owner and not is_admin_viewer:
        raise UnauthorizedException("You can only delete your own uploads")

    await soft_delete_upload(upload, db)
    folder_path = os.path.join(ATTACHMENTS_DIR, UPLOAD_SUBFOLDER)
    delete_file(folder_path, upload.file_name)

    logger.info(f"Delete letter upload {upload_id} process ended")