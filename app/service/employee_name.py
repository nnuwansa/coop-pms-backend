from logging import getLogger
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from crud.employee_name import save_employee_name, get_employee_name_by_id, get_employee_names, \
    get_all_employee_names, update_employee_name, delete_employee_name
from db.models.models import EmployeeName
from exception.exception import NoDataFoundException, DuplicateEntryException
from models.employee_name import EmployeeNameModelIn, EmployeeNameModelUpdate, EmployeeNameModelOut

logger = getLogger(__name__)


async def create_employee_name(model: EmployeeNameModelIn, db: Session):
    logger.info("Create employee name process started")
    name = EmployeeName(full_name=model.full_name.strip())
    try:
        name_db = await save_employee_name(name, db)
    except IntegrityError as e:
        db.rollback()
        raise DuplicateEntryException("This name already exists in the list")
    return EmployeeNameModelOut.model_validate(name_db)


async def get_employee_name_list_service(db: Session, only_active: bool = True):
    names = await (get_employee_names(db) if only_active else get_all_employee_names(db))
    return [EmployeeNameModelOut.model_validate(n) for n in names]


async def update_employee_name_info(name_id: int, model: EmployeeNameModelUpdate, db: Session):
    name_db = await get_employee_name_by_id(name_id, db)
    if not name_db:
        raise NoDataFoundException(f"Name {name_id} not found")

    name_db.full_name = model.full_name.strip()
    name_db.is_active = model.is_active

    try:
        updated = await update_employee_name(name_db, db)
    except IntegrityError:
        db.rollback()
        raise DuplicateEntryException("This name already exists in the list")

    return EmployeeNameModelOut.model_validate(updated)


async def delete_employee_name_info(name_id: int, db: Session):
    name_db = await get_employee_name_by_id(name_id, db)
    if not name_db:
        raise NoDataFoundException(f"Name {name_id} not found")
    await delete_employee_name(name_db, db)