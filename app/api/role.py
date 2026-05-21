import logging

from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED

from db.session import DbSession
from models.response import GenericResponse
from models.role import RoleModelIn, RolePermissionUpdateRequest
from service.role import create_role, update_role_info, soft_delete_role_info, get_active_roles, \
    update_role_permissions_service, get_role_permissions
from utils.auth import get_current_user, has_permission

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/role",
    tags=["Role"],
    dependencies=[Depends(get_current_user)]
)


@router.post("/", status_code=HTTP_201_CREATED, response_model=GenericResponse)
async def create_role_endpoint(role: RoleModelIn, db: DbSession, _=Depends(has_permission("user.view"))):
    logger.debug(f'Request to create role: {role}')
    role_response = await create_role(role, db)

    return GenericResponse(success=True, message="Role created successfully", data=role_response)


@router.get("/list", response_model=GenericResponse)
async def get_active_roles_endpoint(db: DbSession):
    logger.debug('Request to fetch all active roles')
    active_roles = await get_active_roles(db)

    return GenericResponse(success=True, message="Roles fetched successfully", data=active_roles)


@router.put("/{role_id}", response_model=GenericResponse)
async def update_role_endpoint(role_id: int, role_model: RoleModelIn, db: DbSession,
                               _=Depends(has_permission("user.view"))):
    logger.debug(f'Request to update role {role_id} with data: {role_model}')
    updated_role = await update_role_info(role_id, role_model, db)

    return GenericResponse(success=True, message="Role updated successfully", data=updated_role)


@router.delete("/{role_id}", response_model=GenericResponse)
async def delete_role_endpoint(role_id: int, db: DbSession, _=Depends(has_permission("user.view"))):
    logger.debug(f'Request to soft delete role {role_id}')
    deleted_role = await soft_delete_role_info(role_id, db)

    return GenericResponse(success=True, message="Role deleted successfully", data=deleted_role)


@router.put("/{role_id}/permissions", response_model=GenericResponse)
async def update_role_permissions_endpoint(role_id: int, request: RolePermissionUpdateRequest, db: DbSession,
                                           _=Depends(has_permission("user.view"))):
    logger.debug(f'Request to update permissions for role {role_id}: {request}')
    await update_role_permissions_service(role_id, request.permission_ids, db)
    return GenericResponse(
        success=True,
        message=f"Permissions for role {role_id} updated successfully"
    )


@router.get("/{role_id}/permissions", response_model=GenericResponse)
async def get_role_permissions_endpoint(role_id: int, db: DbSession, _=Depends(has_permission("user.view"))):
    logger.debug(f'Request to fetch permissions for role {role_id}')
    permissions = await get_role_permissions(role_id, db)
    return GenericResponse(
        success=True,
        message=f"Permissions for role {role_id} fetched successfully",
        data=permissions
    )
