from logging import getLogger

from sqlalchemy.orm import Session

from db.models.models import Role, RolePermission

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
