import logging

from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED

from db.session import DbSession
from models.permission import PermissionModelIn
from models.response import GenericResponse
from service.permission import create_permission, update_permission_info, delete_permission_info, get_permissions, \
    get_permission
from utils.auth import has_permission

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/permission",
    tags=["Permission"],
    dependencies=[Depends(has_permission("user.view"))]
)


@router.post("/", status_code=HTTP_201_CREATED, response_model=GenericResponse)
async def create_permission_endpoint(permission: PermissionModelIn, db: DbSession):
    logger.debug(f'Request to create permission: {permission}')
    permission_response = await create_permission(permission, db)
    return GenericResponse(success=True, message="Permission created successfully", data=permission_response)


@router.get("/list", response_model=GenericResponse)
async def get_permissions_endpoint(db: DbSession):
    logger.debug('Request to fetch all permissions')
    permissions = await get_permissions(db)
    return GenericResponse(success=True, message="Permissions fetched successfully", data=permissions)


@router.get("/{permission_id}", response_model=GenericResponse)
async def get_permission_endpoint(permission_id: int, db: DbSession):
    logger.debug(f'Request to fetch permission with ID {permission_id}')
    permission = await get_permission(permission_id, db)
    return GenericResponse(success=True, message="Permission fetched successfully", data=permission)


@router.put("/{permission_id}", response_model=GenericResponse)
async def update_permission_endpoint(permission_id: int, permission_model: PermissionModelIn, db: DbSession):
    logger.debug(f'Request to update permission {permission_id} with data: {permission_model}')
    updated_permission = await update_permission_info(permission_id, permission_model, db)
    return GenericResponse(success=True, message="Permission updated successfully", data=updated_permission)


@router.delete("/{permission_id}", response_model=GenericResponse)
async def delete_permission_endpoint(permission_id: int, db: DbSession):
    logger.debug(f'Request to delete permission {permission_id}')
    deleted_permission = await delete_permission_info(permission_id, db)
    return GenericResponse(success=True, message="Permission deleted successfully", data=deleted_permission)
