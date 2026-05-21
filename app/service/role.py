from logging import getLogger

from sqlalchemy.orm import Session

from crud.permission import count_permissions
from crud.role import save_role, get_all_active_roles, get_role_by_id, update_role, update_role_permissions
from db.models.models import Role
from exception.exception import NoDataFoundException
from models.role import RoleModelIn, RoleModelOut

logger = getLogger(__name__)


async def create_role(role_model: RoleModelIn, db: Session):
    logger.info("Create role process started")

    role = Role(
        name=role_model.name,
        description=role_model.description
    )

    role_db = await save_role(role, db)
    role_response = RoleModelOut.model_validate(role_db)

    logger.info("Create role process end")
    return role_response


async def get_active_roles(db: Session):
    logger.info("Fetching active roles process started")

    roles = await get_all_active_roles(db)

    role_list = [
        RoleModelOut(
            id=role.id,
            name=role.name,
            description=role.description,
            permission_count=len(role.permissions) if role.permissions else 0
        ) for role in roles
    ]

    logger.info("Fetching active roles process end")
    return role_list


async def update_role_info(role_id: int, role_model: RoleModelIn, db: Session):
    logger.info(f"Update role process started for role ID {role_id}")

    role_db = await get_role_by_id(role_id, db)
    if not role_db:
        raise NoDataFoundException(f"Role with ID {role_id} not found for update")

    update_data = role_model.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role_db, field, value)

    updated_role = await update_role(role_db, db)
    role_response = RoleModelOut.model_validate(updated_role)

    logger.info(f"Update role process end for role ID {role_id}")
    return role_response


async def soft_delete_role_info(role_id: int, db: Session):
    logger.info(f"Soft delete role process started for role ID {role_id}")

    role_db = await get_role_by_id(role_id, db)
    if not role_db:
        raise NoDataFoundException(f"Role with ID {role_id} not found for delete")

    role_db.is_active = False
    updated_role = await update_role(role_db, db)
    role_response = RoleModelOut.model_validate(updated_role)

    logger.info(f"Soft delete role process end for role ID {role_id}")
    return role_response


async def update_role_permissions_service(role_id: int, permission_ids: list[int], db: Session):
    logger.info(f"Update role permissions started for role ID {role_id}")

    role = await get_role_by_id(role_id, db)
    if not role:
        raise NoDataFoundException(f"Role with ID {role_id} not found")

    if permission_ids:
        permission_count = await count_permissions(permission_ids, db)
        if permission_count != len(permission_ids):
            raise NoDataFoundException("One or more permission IDs do not exist")

        await update_role_permissions(role_id, permission_ids, db)

    logger.info(f"Update role permissions end for role ID {role_id}")


async def get_role_permissions(role_id: int, db: Session):
    logger.info(f"Get role permissions started for role ID {role_id}")

    role = await get_role_by_id(role_id, db)
    if not role:
        raise NoDataFoundException(f"Role with ID {role_id} not found")

    permission_ids = [permission.id for permission in role.permissions]

    logger.info(f"Get role permissions end for role ID {role_id}")
    return permission_ids
