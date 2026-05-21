from logging import getLogger

from sqlalchemy.orm import Session

from crud.department import save_department, get_all_active_departments, get_department_by_id, update_department
from db.models.models import Department
from exception.exception import NoDataFoundException
from models.department import DepartmentModelIn, DepartmentModelOut

logger = getLogger(__name__)


async def create_department(department_model: DepartmentModelIn, db: Session):
    logger.info("Create department process started")

    department = Department(
        name=department_model.name
    )

    department_db = await save_department(department, db)
    department_response = DepartmentModelOut.model_validate(department_db)

    logger.info("Create department process end")
    return department_response


async def get_active_departments(db: Session):
    logger.info("Fetching active departments process started")

    departments = await get_all_active_departments(db)

    department_list = [
        DepartmentModelOut.model_validate(dept) for dept in departments
    ]

    logger.info("Fetching active departments process end")
    return department_list


async def update_department_info(department_id: int, department_model: DepartmentModelIn, db: Session):
    logger.info(f"Update department process started for department ID {department_id}")

    department_db = await get_department_by_id(department_id, db)
    if not department_db:
        raise NoDataFoundException(f"Department with ID {department_id} not found for update")

    update_data = department_model.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(department_db, field, value)

    updated_dept = await update_department(department_db, db)
    department_response = DepartmentModelOut.model_validate(updated_dept)

    logger.info(f"Update department process end for department ID {department_id}")
    return department_response


async def soft_delete_department_info(department_id: int, db: Session):
    logger.info(f"Soft delete department process started for department ID {department_id}")

    department_db = await get_department_by_id(department_id, db)
    if not department_db:
        raise NoDataFoundException(f"Department with ID {department_id} not found for delete")

    department_db.is_active = False
    updated_dept = await update_department(department_db, db)
    department_response = DepartmentModelOut.model_validate(updated_dept)

    logger.info(f"Soft delete department process end for department ID {department_id}")
    return department_response
