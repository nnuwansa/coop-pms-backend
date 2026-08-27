import logging
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile
from fastapi.params import Form, File

from db.session import DbSession
from models.response import GenericResponse
from models.system_user import SystemUserWithPermissionsModelOut
from service.letter_upload import (
    create_upload_service, list_my_uploads_service, list_all_uploads_service, delete_upload_service,
)
from utils.auth import get_current_user, has_permission

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/letter-upload",
    tags=["Letter Upload Collection"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/", response_model=GenericResponse)
async def upload_letter_file_api(
        db: DbSession,
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user),
        title: str = Form(...),
        description: Optional[str] = Form(None),
        file: UploadFile = File(...),
        _=Depends(has_permission("letter.upload_collection")),
):
    logger.debug(f"Request to upload a letter file: {title}")
    result = await create_upload_service(title, description, file, current_user, db)
    return GenericResponse(data=result, message="File uploaded successfully")


@router.get("/mine", response_model=GenericResponse)
async def list_my_uploads_api(
        db: DbSession,
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user),
        _=Depends(has_permission("letter.upload_collection")),
):
    logger.debug("Request to list my letter uploads")
    result = await list_my_uploads_service(current_user, db)
    return GenericResponse(data=result, message="Your uploads fetched successfully")


@router.get("/all", response_model=GenericResponse)
async def list_all_uploads_api(
        db: DbSession,
        _=Depends(has_permission("letter.upload_collection_view")),
):
    logger.debug("Request to list all letter uploads")
    result = await list_all_uploads_service(db)
    return GenericResponse(data=result, message="All uploads fetched successfully")


@router.delete("/{upload_id}", response_model=GenericResponse)
async def delete_upload_api(
        upload_id: int,
        db: DbSession,
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user),
):
    logger.debug(f"Request to delete letter upload {upload_id}")
    await delete_upload_service(upload_id, current_user, db)
    return GenericResponse(message="Upload deleted successfully")