# from logging import getLogger
#
# from sqlalchemy.orm import Session
#
# from db.models.models import Role, RolePermission
#
# logger = getLogger(__name__)
#
#
# async def save_role(role: Role, db: Session):
#     db.add(role)
#     db.commit()
#     db.refresh(role)
#     return role
#
#
# async def get_role_by_id(role_id: int, db: Session):
#     return db.query(Role).filter(Role.id == role_id).first()
#
#
# async def get_all_active_roles(db: Session):
#     return db.query(Role).filter(Role.is_active).all()
#
#
# async def update_role(role: dict, db: Session):
#     db.commit()
#     db.refresh(role)
#     return role
#
#
# async def update_role_permissions(role_id: int, permission_ids: list[int], db: Session):
#     db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
#
#     role_permissions = []
#     for permission_id in permission_ids:
#         role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
#         role_permissions.append(role_permission)
#
#     db.add_all(role_permissions)
#     db.commit()



from logging import getLogger

from sqlalchemy.orm import Session

from db.models.models import Role, RolePermission, SystemUser

logger = getLogger(__name__)


async def save_role(role: Role, db: Session):
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


async def get_role_by_id(role_id: int, db: Session):
    return db.query(Role).filter(Role.id == role_id).first()


async def get_all_active_roles(db: Session):
    return db.query(Role).filter(Role.is_active).all()


async def update_role(role: dict, db: Session):
    db.commit()
    db.refresh(role)
    return role


async def update_role_permissions(role_id: int, permission_ids: list[int], db: Session):
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()

    role_permissions = []
    for permission_id in permission_ids:
        role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
        role_permissions.append(role_permission)

    db.add_all(role_permissions)
    db.commit()


async def get_users_by_role_id(role_id: int, db: Session):
    return db.query(SystemUser).filter(SystemUser.role_id == role_id).all()


async def assign_users_to_role(role_id: int, user_ids: list[int], db: Session):
    """
    Synchronizes role assignment: users in `user_ids` get this role;
    users who currently hold this role but were left out of `user_ids`
    have it cleared.
    """
    clear_query = db.query(SystemUser).filter(SystemUser.role_id == role_id)
    if user_ids:
        clear_query = clear_query.filter(~SystemUser.id.in_(user_ids))
    clear_query.update({SystemUser.role_id: None}, synchronize_session=False)

    if user_ids:
        db.query(SystemUser).filter(SystemUser.id.in_(user_ids)).update(
            {SystemUser.role_id: role_id}, synchronize_session=False
        )

    db.commit()