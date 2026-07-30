from logging import getLogger
from sqlalchemy.orm import Session
from db.models.models import DepartmentUnit

logger = getLogger(__name__)


async def save_department_unit(unit: DepartmentUnit, db: Session):
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


async def get_department_unit_by_id(unit_id: int, db: Session):
    return db.query(DepartmentUnit).filter(DepartmentUnit.id == unit_id).first()


async def get_units_by_department(department_id: int, db: Session):
    return db.query(DepartmentUnit).filter(
        DepartmentUnit.department_id == department_id,
        DepartmentUnit.is_active
    ).all()


async def update_department_unit(unit: DepartmentUnit, db: Session):
    db.commit()
    db.refresh(unit)
    return unit


async def get_units_by_ids(unit_ids: list[int], db: Session):
    if not unit_ids:
        return []
    return db.query(DepartmentUnit).filter(DepartmentUnit.id.in_(unit_ids)).all()