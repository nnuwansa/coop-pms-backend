import logging
from typing import Optional

from fastapi import APIRouter, Depends, Path

from db.session import DbSession
from models.managed_file import ManagedFileIn
from models.response import GenericResponse
from models.system_user import SystemUserWithPermissionsModelOut
from service.managed_file import (
    create_managed_file_service, list_managed_files_service, list_my_managed_files_service,
    update_managed_file_service, delete_managed_file_service,
)
from utils.auth import get_current_user, has_permission

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/managed-file",
    tags=["File Management"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/", response_model=GenericResponse)
async def create_managed_file_api(
        payload: ManagedFileIn,
        db: DbSession,
        _=Depends(has_permission("file.update")),
):
    logger.debug(f"Request to create managed file: {payload}")
    result = await create_managed_file_service(payload, db)
    return GenericResponse(data=result, message="File created successfully")


@router.get("/list", response_model=GenericResponse)
async def list_managed_files_api(
        db: DbSession,
        _=Depends(has_permission("file.update")),
        department_id: Optional[int] = None,
        department_unit_id: Optional[int] = None,
        assigned_to_id: Optional[int] = None,
):
    logger.debug("Request to list managed files")
    result = await list_managed_files_service(db, department_id, department_unit_id, assigned_to_id)
    return GenericResponse(data=result, message="Files fetched successfully")


@router.get("/mine", response_model=GenericResponse)
async def list_my_managed_files_api(
        db: DbSession,
        current_user: SystemUserWithPermissionsModelOut = Depends(get_current_user),
):
    # NEW — any logged-in user can call this: it only ever returns files
    # assigned specifically to them, which is exactly the scoping the
    # Assignee Status File Name picker needs. No separate permission
    # required beyond being authenticated.
    logger.debug(f"Request to list files assigned to user {current_user.id}")
    result = await list_my_managed_files_service(current_user.id, db)
    return GenericResponse(data=result, message="Your files fetched successfully")


@router.put("/{file_id}", response_model=GenericResponse)
async def update_managed_file_api(
        payload: ManagedFileIn,
        db: DbSession,
        file_id: int = Path(...),
        _=Depends(has_permission("file.update")),
):
    logger.debug(f"Request to update managed file {file_id}")
    result = await update_managed_file_service(file_id, payload, db)
    return GenericResponse(data=result, message="File updated successfully")


@router.delete("/{file_id}", response_model=GenericResponse)
async def delete_managed_file_api(
        db: DbSession,
        file_id: int = Path(...),
        _=Depends(has_permission("file.update")),
):
    logger.debug(f"Request to delete managed file {file_id}")
    await delete_managed_file_service(file_id, db)
    return GenericResponse(message="File deleted successfully")