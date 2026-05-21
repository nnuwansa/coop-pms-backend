import logging

from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED

from db.session import DbSession
from models.department import DepartmentModelIn
from models.response import GenericResponse
from service.department import create_department, update_department_info, soft_delete_department_info, \
    get_active_departments
from utils.auth import get_current_user, has_permission

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/department",
    tags=["Department"],
    dependencies=[Depends(get_current_user)]
)


@router.post("/", status_code=HTTP_201_CREATED, response_model=GenericResponse)
async def create_department_endpoint(department: DepartmentModelIn, db: DbSession,
                                     _=Depends(has_permission("settings.view"))):
    logger.debug(f'Request to create department: {department}')
    department_response = await create_department(department, db)

    return GenericResponse(success=True, message="Department created successfully", data=department_response)


@router.get("/list", response_model=GenericResponse)
async def get_active_departments_endpoint(db: DbSession):
    logger.debug('Request to fetch all active departments')
    active_departments = await get_active_departments(db)

    return GenericResponse(success=True, message="Department fetched successfully", data=active_departments)


@router.put("/{department_id}", response_model=GenericResponse)
async def update_department_endpoint(department_id: int, department_model: DepartmentModelIn, db: DbSession,
                                     _=Depends(has_permission("settings.view"))):
    logger.debug(f'Request to update department {department_id} with data: {department_model}')
    updated_department = await update_department_info(department_id, department_model, db)

    return GenericResponse(success=True, message="Department updated successfully", data=updated_department)


@router.delete("/{department_id}", response_model=GenericResponse)
async def delete_department_endpoint(department_id: int, db: DbSession, _=Depends(has_permission("settings.view"))):
    logger.debug(f'Request to soft delete department {department_id}')
    deleted_department = await soft_delete_department_info(department_id, db)

    return GenericResponse(success=True, message="Department deleted successfully", data=deleted_department)
