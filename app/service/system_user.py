from logging import getLogger

from sqlalchemy.orm import Session

from crud.system_user import save_system_user, get_system_user_by_id, update_system_user, \
    delete_system_user, get_system_users, get_system_users_with_filter, system_user_stats
from db.models.models import SystemUser
from exception.exception import NoDataFoundException
from models.system_user import SystemUserModelIn, SystemUserModelOut, SystemUserModelUpdate, SystemUserModelNamesOut, \
    SystemUserFilter, SystemUserModelOutList
from utils.security import hash_password

logger = getLogger(__name__)


async def create_system_user(user_model: SystemUserModelIn, db: Session):
    logger.info("Create system user process started")

    hash_pwd = await hash_password(user_model.password)
    user = SystemUser(
        email=user_model.email,
        password=hash_pwd,
        first_name=user_model.first_name,
        last_name=user_model.last_name,
        role_id=user_model.role_id,
        department_id=user_model.department_id
    )

    user_db = await save_system_user(user, db)
    user_response = SystemUserModelOut.model_validate(user_db)

    logger.info("Create system user process ended")
    return user_response


async def get_all_system_user_full_names_service(db: Session):
    logger.info("Get all system user full names process started")

    users = await get_system_users(db)
    user_full_names = [
        SystemUserModelNamesOut(
            id=user.id,
            name=f"{user.first_name} {user.last_name}") for user in users
    ]

    logger.info("Get all system user full names process ended")
    return user_full_names


async def update_system_user_info(user_id: int, user_model: SystemUserModelUpdate, db: Session):
    logger.info(f"Update system user {user_id} process started")

    user_db = await get_system_user_by_id(user_id, db)
    if not user_db:
        raise NoDataFoundException(f"User {user_id} not found")

    user_db.email = user_model.email
    user_db.first_name = user_model.first_name
    user_db.last_name = user_model.last_name
    user_db.role_id = user_model.role_id if user_model.role_id else None
    user_db.department_id = user_model.department_id if user_model.department_id else None
    if user_model.password:
        user_db.password = await hash_password(user_model.password)
    user_db.is_active = user_model.is_active

    updated_user = await update_system_user(user_db, db)
    user_response = SystemUserModelOut.model_validate(updated_user)

    logger.info(f"Update system user {user_id} process ended")
    return user_response


async def delete_system_user_info(user_id: int, db: Session):
    logger.info(f"Hard delete system user {user_id} process started")

    user_db = await get_system_user_by_id(user_id, db)
    if not user_db:
        raise NoDataFoundException(f"User {user_id} not found")

    await delete_system_user(user_db, db)
    logger.info(f"Hard delete system user {user_id} process ended")


async def get_list_users(filters: SystemUserFilter, page: int, page_size: int, db: Session):
    logger.info(f"Get list of users process started with filters: {filters}")

    total, users = await get_system_users_with_filter(filters, page, page_size, db)
    user_response = [SystemUserModelOutList(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.name if user.role else None,
        department=user.department.name if user.department else None,
        status='Active' if user.is_active else 'Inactive',
    ) for user in users]

    logger.info("Get list of users process ended")
    return total, user_response


async def get_system_user_stats(db: Session):
    logger.info("Get system user stats process started")

    stats = await system_user_stats(db)

    logger.info("Get system user stats process ended")
    return stats
