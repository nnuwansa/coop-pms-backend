from logging import getLogger
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models.models import Designation

logger = getLogger(__name__)


async def save_designation(designation: Designation, db: Session) -> Designation:
    db.add(designation)
    db.commit()
    db.refresh(designation)
    return designation


async def get_designation_by_id(designation_id: int, db: Session) -> Optional[Designation]:
    stmt = select(Designation).where(Designation.id == designation_id)
    return db.execute(stmt).scalar_one_or_none()


async def get_designation_by_name(name: str, db: Session) -> Optional[Designation]:
    stmt = select(Designation).where(Designation.name == name)
    return db.execute(stmt).scalar_one_or_none()


async def get_designations(db: Session):
    stmt = select(Designation).where(Designation.is_active == True).order_by(Designation.name)
    return db.execute(stmt).scalars().all()


async def update_designation(designation: Designation, db: Session) -> Designation:
    db.commit()
    db.refresh(designation)
    return designation


async def delete_designation(designation: Designation, db: Session):
    db.delete(designation)
    db.commit()