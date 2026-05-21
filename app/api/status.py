import logging

from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED

from db.session import DbSession
from models.response import GenericResponse
from models.status import StatusModelIn
from service.status import create_status, get_all_active_statuses_service, update_status_id, delete_status
from utils.auth import get_current_user, has_permission

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/status",
    tags=["Status"],
    dependencies=[Depends(get_current_user)]
)


@router.post("/", status_code=HTTP_201_CREATED, response_model=GenericResponse)
async def create_status_endpoint(status: StatusModelIn, db: DbSession, _=Depends(has_permission("settings.view"))):
    logger.debug(f'Request to create status: {status}')
    status_response = await create_status(status, db)

    return GenericResponse(success=True, message="Status created successfully", data=status_response)


@router.get("/list", response_model=GenericResponse)
async def get_active_statuses_endpoint(db: DbSession):
    logger.debug('Request to fetch all active statuses')
    active_statuses = await get_all_active_statuses_service(db)

    return GenericResponse(success=True, message="Status fetched successfully", data=active_statuses)


@router.put("/{status_id}", response_model=GenericResponse)
async def update_status_endpoint(status_id: int, status_model: StatusModelIn, db: DbSession,
                                 _=Depends(has_permission("settings.view"))):
    logger.debug(f"Request to update status {status_id} with data: {status_model}")
    updated_status = await update_status_id(status_id, status_model, db)

    return GenericResponse(success=True, message="Status updated successfully", data=updated_status)


@router.delete("/{status_id}", response_model=GenericResponse)
async def delete_status_endpoint(status_id: int, db: DbSession, _=Depends(has_permission("settings.view"))):
    logger.debug(f'Request to soft delete status {status_id}')
    deleted_status = await delete_status(status_id, db)

    return GenericResponse(success=True, message="Status deleted successfully", data=deleted_status)
