from logging import getLogger
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models.models import EmployeeName

logger = getLogger(__name__)


async def save_employee_name(name: EmployeeName, db: Session) -> EmployeeName:
    db.add(name)
    db.commit()
    db.refresh(name)
    return name


async def get_employee_name_by_id(name_id: int, db: Session) -> Optional[EmployeeName]:
    stmt = select(EmployeeName).where(EmployeeName.id == name_id)
    return db.execute(stmt).scalar_one_or_none()


async def get_employee_names(db: Session):
    stmt = select(EmployeeName).where(EmployeeName.is_active == True).order_by(EmployeeName.full_name)
    return db.execute(stmt).scalars().all()


async def get_all_employee_names(db: Session):
    """Returns every name regardless of active status — for the admin manager dialog."""
    stmt = select(EmployeeName).order_by(EmployeeName.full_name)
    return db.execute(stmt).scalars().all()


async def update_employee_name(name: EmployeeName, db: Session) -> EmployeeName:
    db.commit()
    db.refresh(name)
    return name


async def delete_employee_name(name: EmployeeName, db: Session):
    db.delete(name)
    db.commit()