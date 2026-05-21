from logging import getLogger

from db.models.models import Department

logger = getLogger(__name__)


async def save_department(department: Department, db):
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


async def get_department_by_id(department_id: int, db):
    return db.query(Department).filter(Department.id == department_id).first()


async def get_all_active_departments(db):
    return db.query(Department).filter(Department.is_active).all()


async def update_department(department: dict, db):
    db.commit()
    db.refresh(department)
    return department
