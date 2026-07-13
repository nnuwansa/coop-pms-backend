from logging import getLogger
from typing import Optional

from sqlalchemy.orm import Session

from crud.system_user import save_system_user, get_system_user_by_id, update_system_user, \
    delete_system_user, get_system_users, get_system_users_with_filter, system_user_stats
from crud.system_user_history import save_user_history, get_user_history
from db.models.models import SystemUser, Role, Department,Designation
from exception.exception import NoDataFoundException
from models.system_user import SystemUserModelIn, SystemUserModelOut, SystemUserModelUpdate, SystemUserModelNamesOut, \
    SystemUserFilter, SystemUserModelOutList, SystemUserHistoryOut
from utils.security import hash_password

from sqlalchemy.exc import IntegrityError
from exception.exception import NoDataFoundException, ValidationException



logger = getLogger(__name__)


def _display(value) -> str:
    """Renders None/empty values as an em dash so history reads cleanly."""
    if value is None or value == "":
        return "—"
    return str(value)


async def create_system_user(user_model: SystemUserModelIn, db: Session, performed_by: Optional[str] = None):
    logger.info("Create system user process started")

    hash_pwd = await hash_password(user_model.password)
    user = SystemUser(
        email=user_model.email,
        password=hash_pwd,
        first_name=user_model.first_name,
        last_name=user_model.last_name,
        employee_id=user_model.employee_id,
        nic=user_model.nic,
        designation_id=user_model.designation_id,
        role_id=user_model.role_id,
        department_id=user_model.department_id
    )

    user_db = await save_system_user(user, db)

    details = [f"Account created for {user_db.email}"]
    if user_db.employee_id:
        details.append(f"Employee ID: {user_db.employee_id}")
    if user_db.designation:
        details.append(f"Designation: {user_db.designation.name}")

    await save_user_history(
        user_id=user_db.id,
        action="Created",
        description="; ".join(details),
        performed_by=performed_by or user_db.email,
        db=db
    )

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


async def update_system_user_info(
        user_id: int,
        user_model: SystemUserModelUpdate,
        db: Session,
        performed_by: Optional[str] = None
):
    logger.info(f"Update system user {user_id} process started")

    user_db = await get_system_user_by_id(user_id, db)
    if not user_db:
        raise NoDataFoundException(f"User {user_id} not found")

    changes = []

    if user_db.email != user_model.email:
        changes.append(f"email changed from '{_display(user_db.email)}' to '{_display(user_model.email)}'")
    if user_db.first_name != user_model.first_name:
        changes.append(f"first name changed from '{_display(user_db.first_name)}' to '{_display(user_model.first_name)}'")
    if user_db.last_name != user_model.last_name:
        changes.append(f"last name changed from '{_display(user_db.last_name)}' to '{_display(user_model.last_name)}'")
    if user_db.employee_id != user_model.employee_id:
        changes.append(f"employee ID changed from '{_display(user_db.employee_id)}' to '{_display(user_model.employee_id)}'")
    if user_db.nic != user_model.nic:
        changes.append(f"NIC changed from '{_display(user_db.nic)}' to '{_display(user_model.nic)}'")
    if user_db.designation_id != user_model.designation_id:
        changes.append(f"designation changed from '{_display(user_db.designation)}' to '{_display(user_model.designation)}'")
    if user_model.password:
        changes.append("password changed")
    if user_db.is_active != user_model.is_active:
        changes.append(f"status changed to {'Active' if user_model.is_active else 'Inactive'}")

    # Role: compare by id, but describe by name
    new_role_id = user_model.role_id if user_model.role_id else None
    if user_db.role_id != new_role_id:
        old_role_name = user_db.role.name if user_db.role else "None"
        new_role = db.query(Role).filter(Role.id == new_role_id).first() if new_role_id else None
        new_role_name = new_role.name if new_role else "None"
        changes.append(f"role changed from '{old_role_name}' to '{new_role_name}'")

    # Department: compare by id, but describe by name
    new_department_id = user_model.department_id if user_model.department_id else None
    if user_db.department_id != new_department_id:
        old_department_name = user_db.department.name if user_db.department else "None"
        new_department = db.query(Department).filter(
            Department.id == new_department_id).first() if new_department_id else None
        new_department_name = new_department.name if new_department else "None"
        changes.append(f"department changed from '{old_department_name}' to '{new_department_name}'")

    # Designation: compare by id, but describe by name
    new_designation_id = user_model.designation_id if user_model.designation_id else None
    if user_db.designation_id != new_designation_id:
        old_designation_name = user_db.designation.name if user_db.designation else "None"
        new_designation = db.query(Designation).filter(
            Designation.id == new_designation_id).first() if new_designation_id else None
        new_designation_name = new_designation.name if new_designation else "None"
        changes.append(f"designation changed from '{old_designation_name}' to '{new_designation_name}'")


    user_db.email = user_model.email
    user_db.first_name = user_model.first_name
    user_db.last_name = user_model.last_name
    user_db.employee_id = user_model.employee_id
    user_db.nic = user_model.nic
    user_db.designation_id = new_designation_id
    user_db.role_id = new_role_id
    user_db.department_id = new_department_id
    if user_model.password:
        user_db.password = await hash_password(user_model.password)
    user_db.is_active = user_model.is_active

    updated_user = await update_system_user(user_db, db)

    await save_user_history(
        user_id=updated_user.id,
        action="Updated",
        description="; ".join(changes) if changes else "Profile saved (no field changes detected)",
        performed_by=performed_by,
        db=db
    )

    user_response = SystemUserModelOut.model_validate(updated_user)

    logger.info(f"Update system user {user_id} process ended")
    return user_response


# async def delete_system_user_info(user_id: int, db: Session, performed_by: Optional[str] = None):
#     logger.info(f"Hard delete system user {user_id} process started")
#
#     user_db = await get_system_user_by_id(user_id, db)
#     if not user_db:
#         raise NoDataFoundException(f"User {user_id} not found")
#
#     await save_user_history(
#         user_id=user_db.id,
#         action="Deleted",
#         description=f"Account deleted for {user_db.email}",
#         performed_by=performed_by,
#         db=db
#     )
#
#     await delete_system_user(user_db, db)
#     logger.info(f"Hard delete system user {user_id} process ended")


async def delete_system_user_info(user_id: int, db: Session, performed_by: Optional[str] = None):
    logger.info(f"Hard delete system user {user_id} process started")

    user_db = await get_system_user_by_id(user_id, db)
    if not user_db:
        raise NoDataFoundException(f"User {user_id} not found")

    user_email = user_db.email  # capture before the row is gone

    # Attempt the delete FIRST. Only log history if it actually succeeds,
    # so a failed delete (e.g. blocked by a foreign key constraint because
    # the user is referenced by letters/remarks/assignments) never leaves
    # behind a misleading "Deleted" history entry.
    try:
        await delete_system_user(user_db, db)
    except IntegrityError:
        db.rollback()
        logger.warning(f"Delete blocked by foreign key constraint for user {user_id}")
        raise ValidationException(
            "This user can't be deleted because they're still linked to letters, "
            "remarks, or assignments. Reassign or remove those references first, "
            "or deactivate the account instead of deleting it."
        )

    await save_user_history(
        user_id=user_id,
        action="Deleted",
        description=f"Account deleted for {user_email}",
        performed_by=performed_by,
        db=db
    )

    logger.info(f"Hard delete system user {user_id} process ended")

async def get_list_users(filters: SystemUserFilter, page: int, page_size: int, db: Session):
    logger.info(f"Get list of users process started with filters: {filters}")

    total, users = await get_system_users_with_filter(filters, page, page_size, db)
    user_response = [SystemUserModelOutList(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        employee_id=user.employee_id,
        nic=user.nic,
        designation=user.designation.name if user.designation else None,
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


async def get_user_history_service(user_id: int, db: Session):
    logger.info(f"Get history for system user {user_id} process started")

    history = await get_user_history(user_id, db)
    history_response = [SystemUserHistoryOut.model_validate(h) for h in history]

    logger.info(f"Get history for system user {user_id} process ended")
    return history_response