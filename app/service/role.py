
from logging import getLogger

from sqlalchemy.orm import Session

from crud.permission import count_permissions
from crud.role import save_role, get_all_active_roles, get_role_by_id, update_role, update_role_permissions, \
    get_users_by_role_id, assign_users_to_role, get_role_status_ids, update_role_status_permissions
from crud.system_user import get_all_system_users_basic
from db.models.models import Role
from exception.exception import NoDataFoundException
from models.role import RoleModelIn, RoleModelOut, AssignableUserOut, RolePermissionsOut

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


async def update_role_permissions_service(
        role_id: int, permission_ids: list[int], status_ids: list[int], db: Session   # NEW param
):
    logger.info(f"Update role permissions started for role ID {role_id}")

    role = await get_role_by_id(role_id, db)
    if not role:
        raise NoDataFoundException(f"Role with ID {role_id} not found")

    if permission_ids:
        permission_count = await count_permissions(permission_ids, db)
        if permission_count != len(permission_ids):
            raise NoDataFoundException("One or more permission IDs do not exist")
        await update_role_permissions(role_id, permission_ids, db)

    # NEW — only keep status restrictions if "Change Letter Status" is actually granted;
    # otherwise clear any stale status selections
    has_change_status_permission = any(
        p.code == "letter.change_status" for p in role.permissions
    ) if permission_ids else False

    await update_role_status_permissions(
        role_id, status_ids if has_change_status_permission else [], db
    )

    logger.info(f"Update role permissions end for role ID {role_id}")


async def get_role_permissions(role_id: int, db: Session):   # CHANGED return shape
    logger.info(f"Get role permissions started for role ID {role_id}")

    role = await get_role_by_id(role_id, db)
    if not role:
        raise NoDataFoundException(f"Role with ID {role_id} not found")

    permission_ids = [permission.id for permission in role.permissions]
    status_ids = await get_role_status_ids(role_id, db)   # NEW

    logger.info(f"Get role permissions end for role ID {role_id}")
    return RolePermissionsOut(permission_ids=permission_ids, status_ids=status_ids)   # CHANGED

async def get_assignable_users_service(db: Session):
    logger.info("Fetching assignable users for role dialog")

    users = await get_all_system_users_basic(db)
    return [
        AssignableUserOut(
            id=user.id,
            name=f"{user.first_name} {user.last_name}",
            current_role_id=user.role_id,
            current_role_name=user.role.name if user.role else None,
        ) for user in users
    ]


async def get_role_user_ids_service(role_id: int, db: Session):
    logger.info(f"Fetching users currently assigned to role {role_id}")

    role = await get_role_by_id(role_id, db)
    if not role:
        raise NoDataFoundException(f"Role with ID {role_id} not found")

    users = await get_users_by_role_id(role_id, db)
    return [user.id for user in users]


async def assign_users_to_role_service(role_id: int, user_ids: list[int], db: Session):
    logger.info(f"Assigning users {user_ids} to role {role_id}")

    role = await get_role_by_id(role_id, db)
    if not role:
        raise NoDataFoundException(f"Role with ID {role_id} not found")

    await assign_users_to_role(role_id, user_ids, db)