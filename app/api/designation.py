import logging

from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED

from db.session import DbSession
from models.response import GenericResponse
from models.designation import DesignationModelIn, DesignationModelUpdate
from service.designation import create_designation, get_designation_list_service, \
    update_designation_info, delete_designation_info
from utils.auth import get_current_user, has_permission

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/designation",
    tags=["Designation"]
)


@router.post("/", status_code=HTTP_201_CREATED, response_model=GenericResponse)
async def create_designation_endpoint(
        designation: DesignationModelIn,
        db: DbSession,
        _=Depends(has_permission("user.view"))
):
    logger.debug(f'Request to create designation: {designation}')
    designation_response = await create_designation(designation, db)

    return GenericResponse(success=True, message="Designation created successfully", data=designation_response)


@router.get("/list", response_model=GenericResponse)
async def get_designation_list_endpoint(
        db: DbSession,
        _=Depends(get_current_user)
):
    logger.debug('Request to fetch designation list')
    designations = await get_designation_list_service(db)

    return GenericResponse(success=True, message="Designation list fetched successfully", data=designations)


@router.put("/{designation_id}", response_model=GenericResponse)
async def update_designation_endpoint(
        designation_id: int,
        designation: DesignationModelUpdate,
        db: DbSession,
        _=Depends(has_permission("user.view"))
):
    logger.debug(f'Request to update designation {designation_id}')
    updated = await update_designation_info(designation_id, designation, db)

    return GenericResponse(success=True, message="Designation updated successfully", data=updated)


@router.delete("/{designation_id}", response_model=GenericResponse)
async def delete_designation_endpoint(
        designation_id: int,
        db: DbSession,
        _=Depends(has_permission("user.view"))
):
    logger.debug(f'Request to delete designation {designation_id}')
    await delete_designation_info(designation_id, db)

    return GenericResponse(success=True, message="Designation deleted successfully")



@router.get("/public-list", response_model=GenericResponse)
async def get_public_designation_list_endpoint(db: DbSession):
    designations = await get_designation_list_service(db)
    return GenericResponse(success=True, message="Designation list fetched successfully", data=designations)