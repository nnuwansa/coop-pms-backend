# from logging import getLogger
#
# from sqlalchemy import select, and_, func, desc
# from sqlalchemy.exc import IntegrityError
# from sqlalchemy.orm import Session
#
# from db.models.models import SystemUser
# from exception.exception import DuplicateEntryException
# from models.system_user import SystemUserFilter
#
# logger = getLogger(__name__)
#
#
# async def save_system_user(system_user: SystemUser, db):
#     try:
#         db.add(system_user)
#         db.commit()
#         db.refresh(system_user)
#     except IntegrityError as e:
#         db.rollback()
#         if "Duplicate entry" in str(e.orig):
#             raise DuplicateEntryException("Email already exists")
#         raise e
#     return system_user
#
#
# async def get_system_user_by_id(user_id: int, db: Session):
#     return db.query(SystemUser).filter(SystemUser.id == user_id).first()
#
#
# async def get_system_users(db: Session):
#     return db.query(SystemUser).filter(SystemUser.is_active).all()
#
#
# async def update_system_user(user_data: dict, db: Session):
#     try:
#         db.commit()
#         db.refresh(user_data)
#     except IntegrityError as e:
#         db.rollback()
#         if "Duplicate entry" in str(e.orig):
#             raise DuplicateEntryException("Email already exists")
#         raise e
#     return user_data
#
#
# async def delete_system_user(user: SystemUser, db: Session):
#     db.delete(user)
#     db.commit()
#
#
# async def get_system_users_with_filter(filters: SystemUserFilter, page: int, page_size: int, db: Session):
#     stmt = select(SystemUser)
#     total_stmt = select(func.count()).select_from(SystemUser)
#
#     if filters:
#         conditions = []
#         if filters.id:
#             conditions.append(SystemUser.id == filters.id)
#         if filters.email:
#             conditions.append(SystemUser.email.ilike(f"%{filters.email}%"))
#         if filters.first_name:
#             conditions.append(SystemUser.first_name.ilike(f"%{filters.first_name}%"))
#         if filters.last_name:
#             conditions.append(SystemUser.last_name.ilike(f"%{filters.last_name}%"))
#         if filters.department_id:
#             conditions.append(SystemUser.department_id == filters.department_id)
#         if filters.role_id:
#             conditions.append(SystemUser.role_id == filters.role_id)
#         if filters.is_active is not None:
#             conditions.append(SystemUser.is_active == filters.is_active)
#
#         stmt = stmt.where(and_(*conditions))
#         total_stmt = total_stmt.where(and_(*conditions))
#
#     stmt = stmt.order_by(desc(SystemUser.create_datetime))
#     stmt = stmt.offset((page - 1) * page_size).limit(page_size)
#
#     result = db.execute(stmt)
#     total_result = db.execute(total_stmt)
#
#     users = result.scalars().all()
#     total = total_result.scalar_one()
#
#     return total, users
#
#
# async def system_user_stats(db: Session):
#     stmt_active = select(func.count()).select_from(SystemUser).where(SystemUser.is_active)
#     stmt_inactive = select(func.count()).select_from(SystemUser).where(SystemUser.is_active == False)
#     stmt_total = select(func.count()).select_from(SystemUser)
#
#     result_active = db.execute(stmt_active).scalar_one()
#     result_inactive = db.execute(stmt_inactive).scalar_one()
#     result_total = db.execute(stmt_total).scalar_one()
#
#     stats = {
#         "active_users": result_active,
#         "inactive_users": result_inactive,
#         "total_users": result_total
#     }
#     return stats
#
#
# async def get_user_by_email(email: str, db: Session):
#     return db.query(SystemUser).filter(SystemUser.email == email).first()
#
#
# async def get_active_user_by_id(user_id: int, db: Session):
#     user = db.query(SystemUser).filter(SystemUser.id == user_id).first()
#     if user and user.is_active:
#         return user
#     return None


#
# from logging import getLogger
#
# from sqlalchemy import select, and_, func, desc
# from sqlalchemy.exc import IntegrityError
# from sqlalchemy.orm import Session
#
# from db.models.models import SystemUser
# from exception.exception import DuplicateEntryException
# from models.system_user import SystemUserFilter
#
# logger = getLogger(__name__)
#
#
# async def save_system_user(system_user: SystemUser, db):
#     try:
#         db.add(system_user)
#         db.commit()
#         db.refresh(system_user)
#     except IntegrityError as e:
#         db.rollback()
#         if "Duplicate entry" in str(e.orig):
#             raise DuplicateEntryException("Email already exists")
#         raise e
#     return system_user
#
#
# async def get_system_user_by_id(user_id: int, db: Session):
#     return db.query(SystemUser).filter(SystemUser.id == user_id).first()
#
#
# async def get_system_users(db: Session):
#     return db.query(SystemUser).filter(SystemUser.is_active).all()
#
#
# async def get_all_system_users_basic(db: Session):
#     """
#     Returns every registered user regardless of active status — used to
#     populate the "assign to users" picker on the role dialogs, since a
#     user may need a role assigned before their account is activated.
#     """
#     return db.query(SystemUser).order_by(SystemUser.first_name, SystemUser.last_name).all()
#
#
# async def update_system_user(user_data: dict, db: Session):
#     try:
#         db.commit()
#         db.refresh(user_data)
#     except IntegrityError as e:
#         db.rollback()
#         if "Duplicate entry" in str(e.orig):
#             raise DuplicateEntryException("Email already exists")
#         raise e
#     return user_data
#
#
# async def delete_system_user(user: SystemUser, db: Session):
#     db.delete(user)
#     db.commit()
#
#
# async def get_system_users_with_filter(filters: SystemUserFilter, page: int, page_size: int, db: Session):
#     stmt = select(SystemUser)
#     total_stmt = select(func.count()).select_from(SystemUser)
#
#     if filters:
#         conditions = []
#         if filters.id:
#             conditions.append(SystemUser.id == filters.id)
#         if filters.email:
#             conditions.append(SystemUser.email.ilike(f"%{filters.email}%"))
#         if filters.first_name:
#             conditions.append(SystemUser.first_name.ilike(f"%{filters.first_name}%"))
#         if filters.last_name:
#             conditions.append(SystemUser.last_name.ilike(f"%{filters.last_name}%"))
#         if filters.department_id:
#             conditions.append(SystemUser.department_id == filters.department_id)
#         if filters.role_id:
#             conditions.append(SystemUser.role_id == filters.role_id)
#         if filters.is_active is not None:
#             conditions.append(SystemUser.is_active == filters.is_active)
#
#         stmt = stmt.where(and_(*conditions))
#         total_stmt = total_stmt.where(and_(*conditions))
#
#     stmt = stmt.order_by(desc(SystemUser.create_datetime))
#     stmt = stmt.offset((page - 1) * page_size).limit(page_size)
#
#     result = db.execute(stmt)
#     total_result = db.execute(total_stmt)
#
#     users = result.scalars().all()
#     total = total_result.scalar_one()
#
#     return total, users
#
#
# async def system_user_stats(db: Session):
#     stmt_active = select(func.count()).select_from(SystemUser).where(SystemUser.is_active)
#     stmt_inactive = select(func.count()).select_from(SystemUser).where(SystemUser.is_active == False)
#     stmt_total = select(func.count()).select_from(SystemUser)
#
#     result_active = db.execute(stmt_active).scalar_one()
#     result_inactive = db.execute(stmt_inactive).scalar_one()
#     result_total = db.execute(stmt_total).scalar_one()
#
#     stats = {
#         "active_users": result_active,
#         "inactive_users": result_inactive,
#         "total_users": result_total
#     }
#     return stats
#
#
# async def get_user_by_email(email: str, db: Session):
#     return db.query(SystemUser).filter(SystemUser.email == email).first()
#
#
# async def get_active_user_by_id(user_id: int, db: Session):
#     user = db.query(SystemUser).filter(SystemUser.id == user_id).first()
#     if user and user.is_active:
#         return user
#     return None



from logging import getLogger

from sqlalchemy import select, and_, func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.models.models import SystemUser, RefreshToken, LetterAssignee
from exception.exception import DuplicateEntryException
from models.system_user import SystemUserFilter

logger = getLogger(__name__)


async def save_system_user(system_user: SystemUser, db):
    try:
        db.add(system_user)
        db.commit()
        db.refresh(system_user)
    except IntegrityError as e:
        db.rollback()
        if "Duplicate entry" in str(e.orig):
            raise DuplicateEntryException("Email already exists")
        raise e
    return system_user


async def get_system_user_by_id(user_id: int, db: Session):
    return db.query(SystemUser).filter(SystemUser.id == user_id).first()


async def get_system_users(db: Session):
    return db.query(SystemUser).filter(SystemUser.is_active).all()


async def get_all_system_users_basic(db: Session):
    """
    Returns every registered user regardless of active status — used to
    populate the "assign to users" picker on the role dialogs, since a
    user may need a role assigned before their account is activated.
    """
    return db.query(SystemUser).order_by(SystemUser.first_name, SystemUser.last_name).all()


async def update_system_user(user_data: dict, db: Session):
    try:
        db.commit()
        db.refresh(user_data)
    except IntegrityError as e:
        db.rollback()
        if "Duplicate entry" in str(e.orig):
            raise DuplicateEntryException("Email already exists")
        raise e
    return user_data


async def delete_system_user(user: SystemUser, db: Session):
    """
    Hard-deletes a system user. Any records in other tables that hold a
    foreign key to this user (refresh tokens, letter assignments) are
    cleaned up first so the delete never fails with an IntegrityError.
    Only the *link* to the user is removed — the letters themselves, and
    any other assignees on them, are left untouched.
    """
    try:
        db.query(RefreshToken).filter(RefreshToken.user_id == user.id).delete(synchronize_session=False)
        db.query(LetterAssignee).filter(LetterAssignee.assignee_id == user.id).delete(synchronize_session=False)

        db.delete(user)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Failed to delete system user {user.id}: {e}")
        raise e


async def get_system_users_with_filter(filters: SystemUserFilter, page: int, page_size: int, db: Session):
    stmt = select(SystemUser)
    total_stmt = select(func.count()).select_from(SystemUser)

    if filters:
        conditions = []
        if filters.id:
            conditions.append(SystemUser.id == filters.id)
        if filters.email:
            conditions.append(SystemUser.email.ilike(f"%{filters.email}%"))
        if filters.first_name:
            conditions.append(SystemUser.first_name.ilike(f"%{filters.first_name}%"))
        if filters.last_name:
            conditions.append(SystemUser.last_name.ilike(f"%{filters.last_name}%"))
        if filters.department_id:
            conditions.append(SystemUser.department_id == filters.department_id)
        if filters.role_id:
            conditions.append(SystemUser.role_id == filters.role_id)
        if filters.is_active is not None:
            conditions.append(SystemUser.is_active == filters.is_active)

        stmt = stmt.where(and_(*conditions))
        total_stmt = total_stmt.where(and_(*conditions))

    stmt = stmt.order_by(desc(SystemUser.create_datetime))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = db.execute(stmt)
    total_result = db.execute(total_stmt)

    users = result.scalars().all()
    total = total_result.scalar_one()

    return total, users


async def system_user_stats(db: Session):
    stmt_active = select(func.count()).select_from(SystemUser).where(SystemUser.is_active)
    stmt_inactive = select(func.count()).select_from(SystemUser).where(SystemUser.is_active == False)
    stmt_total = select(func.count()).select_from(SystemUser)

    result_active = db.execute(stmt_active).scalar_one()
    result_inactive = db.execute(stmt_inactive).scalar_one()
    result_total = db.execute(stmt_total).scalar_one()

    stats = {
        "active_users": result_active,
        "inactive_users": result_inactive,
        "total_users": result_total
    }
    return stats


async def get_user_by_email(email: str, db: Session):
    return db.query(SystemUser).filter(SystemUser.email == email).first()


async def get_active_user_by_id(user_id: int, db: Session):
    user = db.query(SystemUser).filter(SystemUser.id == user_id).first()
    if user and user.is_active:
        return user
    return None