import logging

from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED

from db.session import DbSession
from models.response import GenericResponse
from models.employee_name import EmployeeNameModelIn, EmployeeNameModelUpdate
from service.employee_name import create_employee_name, get_employee_name_list_service, \
    update_employee_name_info, delete_employee_name_info
from utils.auth import get_current_user, has_permission

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/employee_name",
    tags=["Employee Name"]
)


@router.post("/", status_code=HTTP_201_CREATED, response_model=GenericResponse)
async def create_employee_name_endpoint(
        name: EmployeeNameModelIn,
        db: DbSession,
        _=Depends(has_permission("user.view"))
):
    logger.debug(f'Request to create employee name: {name}')
    response = await create_employee_name(name, db)
    return GenericResponse(success=True, message="Name added successfully", data=response)


@router.get("/list", response_model=GenericResponse)
async def get_employee_name_list_endpoint(
        db: DbSession,
        _=Depends(get_current_user)
):
    """Admin view — includes inactive names too, for the manager dialog."""
    logger.debug('Request to fetch employee name list (admin)')
    names = await get_employee_name_list_service(db, only_active=False)
    return GenericResponse(success=True, message="Name list fetched successfully", data=names)


@router.get("/public-list", response_model=GenericResponse)
async def get_public_employee_name_list_endpoint(db: DbSession):
    """Public — used by the sign-up page. No auth, active names only."""
    logger.debug('Request to fetch public employee name list')
    names = await get_employee_name_list_service(db, only_active=True)
    return GenericResponse(success=True, message="Name list fetched successfully", data=names)


@router.put("/{name_id}", response_model=GenericResponse)
async def update_employee_name_endpoint(
        name_id: int,
        name: EmployeeNameModelUpdate,
        db: DbSession,
        _=Depends(has_permission("user.view"))
):
    logger.debug(f'Request to update employee name {name_id}')
    updated = await update_employee_name_info(name_id, name, db)
    return GenericResponse(success=True, message="Name updated successfully", data=updated)


@router.delete("/{name_id}", response_model=GenericResponse)
async def delete_employee_name_endpoint(
        name_id: int,
        db: DbSession,
        _=Depends(has_permission("user.view"))
):
    logger.debug(f'Request to delete employee name {name_id}')
    await delete_employee_name_info(name_id, db)
    return GenericResponse(success=True, message="Name deleted successfully")