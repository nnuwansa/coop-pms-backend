from logging import getLogger

from sqlalchemy import func
from sqlalchemy.orm import Session

from db.models.models import Permission

logger = getLogger(__name__)


async def save_permission(permission: Permission, db: Session):
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission


async def get_permission_by_id(permission_id: int, db: Session):
    return db.query(Permission).filter(Permission.id == permission_id).first()


async def get_permission_by_code(code: str, db: Session):
    return db.query(Permission).filter(Permission.code == code).first()


async def get_all_permissions(db: Session):
    return db.query(Permission).all()


async def update_permission(permission: dict, db: Session):
    db.commit()
    db.refresh(permission)
    return permission


async def delete_permission(permission_id: int, db: Session):
    permission = await get_permission_by_id(permission_id, db)
    if permission:
        db.delete(permission)
        db.commit()
    return permission


async def count_permissions(permission_ids: list[int], db: Session):
    permission_count = db.query(func.count(Permission.id)).filter(
        Permission.id.in_(permission_ids)
    ).scalar()

    return permission_count
