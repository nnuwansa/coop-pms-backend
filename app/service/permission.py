from collections import defaultdict
from logging import getLogger

from sqlalchemy.orm import Session

from crud.permission import save_permission, get_all_permissions, get_permission_by_id, update_permission, \
    delete_permission
from db.models.models import Permission
from exception.exception import NoDataFoundException
from models.permission import PermissionModelOut, PermissionModel, PermissionModelIn

logger = getLogger(__name__)


async def create_permission(permission_model: PermissionModelIn, db: Session):
    logger.info("Create permission process started")

    permission = Permission(
        name=permission_model.name,
        code=permission_model.code,
        description=permission_model.description
    )

    permission_db = await save_permission(permission, db)
    permission_response = PermissionModelOut.model_validate(permission_db)

    logger.info("Create permission process end")
    return permission_response


async def get_permissions(db: Session):
    logger.info("Fetching permissions process started")

    permissions = await get_all_permissions(db)

    grouped = defaultdict(list)
    for permission in permissions:
        key = (permission.category, permission.action)
        grouped[key].append(PermissionModel(
            id=permission.id,
            name=permission.name,
            code=permission.code,
            description=permission.description
        ))

    permission_list = [
        PermissionModelOut(
            category=category,
            action=action,
            permissions=perms
        )
        for (category, action), perms in grouped.items()
    ]

    logger.info("Fetching permissions process end")
    return permission_list


async def get_permission(permission_id: int, db: Session):
    logger.info(f"Fetching permission with ID {permission_id} process started")

    permission = await get_permission_by_id(permission_id, db)
    if not permission:
        raise NoDataFoundException(f"Permission with ID {permission_id} not found")

    permission_response = PermissionModelOut.model_validate(permission)

    logger.info(f"Fetching permission with ID {permission_id} process end")
    return permission_response


async def update_permission_info(permission_id: int, permission_model: PermissionModelIn, db: Session):
    logger.info(f"Update permission process started for permission ID {permission_id}")

    permission_db = await get_permission_by_id(permission_id, db)
    if not permission_db:
        raise NoDataFoundException(f"Permission with ID {permission_id} not found for update")

    update_data = permission_model.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(permission_db, field, value)

    updated_permission = await update_permission(permission_db, db)
    permission_response = PermissionModelOut.model_validate(updated_permission)

    logger.info(f"Update permission process end for permission ID {permission_id}")
    return permission_response


async def delete_permission_info(permission_id: int, db: Session):
    logger.info(f"Delete permission process started for permission ID {permission_id}")

    permission_db = await get_permission_by_id(permission_id, db)
    if not permission_db:
        raise NoDataFoundException(f"Permission with ID {permission_id} not found for delete")

    deleted_permission = await delete_permission(permission_id, db)
    if deleted_permission:
        permission_response = PermissionModelOut.model_validate(deleted_permission)
    else:
        permission_response = None

    logger.info(f"Delete permission process end for permission ID {permission_id}")
    return permission_response
