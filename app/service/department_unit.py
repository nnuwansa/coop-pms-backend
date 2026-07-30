# from logging import getLogger
# from sqlalchemy.orm import Session
#
# from crud.department_unit import (
#     save_department_unit, get_department_unit_by_id, get_units_by_department, update_department_unit
# )
# from crud.department import get_department_by_id
# from db.models.models import DepartmentUnit
# from exception.exception import NoDataFoundException
# from models.department_unit import DepartmentUnitModelIn, DepartmentUnitModelOut
#
# logger = getLogger(__name__)
#
#
# async def create_department_unit(department_id: int, model: DepartmentUnitModelIn, db: Session):
#     department = await get_department_by_id(department_id, db)
#     if not department:
#         raise NoDataFoundException(f"Department with ID {department_id} not found")
#
#     unit = DepartmentUnit(department_id=department_id, name=model.name)
#     unit_db = await save_department_unit(unit, db)
#     return DepartmentUnitModelOut.model_validate(unit_db)
#
#
# async def list_department_units(department_id: int, db: Session):
#     units = await get_units_by_department(department_id, db)
#     return [DepartmentUnitModelOut.model_validate(u) for u in units]
#
#
# async def update_department_unit_info(unit_id: int, model: DepartmentUnitModelIn, db: Session):
#     unit_db = await get_department_unit_by_id(unit_id, db)
#     if not unit_db:
#         raise NoDataFoundException(f"Department unit with ID {unit_id} not found")
#
#     unit_db.name = model.name
#     updated = await update_department_unit(unit_db, db)
#     return DepartmentUnitModelOut.model_validate(updated)
#
#
# async def delete_department_unit_info(unit_id: int, db: Session):
#     unit_db = await get_department_unit_by_id(unit_id, db)
#     if not unit_db:
#         raise NoDataFoundException(f"Department unit with ID {unit_id} not found")
#
#     unit_db.is_active = False
#     updated = await update_department_unit(unit_db, db)
#     return DepartmentUnitModelOut.model_validate(updated)



from logging import getLogger
from sqlalchemy.orm import Session

from crud.department_unit import (
    save_department_unit, get_department_unit_by_id, get_units_by_department, update_department_unit
)
from crud.department import get_department_by_id
from db.models.models import DepartmentUnit
from exception.exception import NoDataFoundException
from models.department_unit import DepartmentUnitModelIn, DepartmentUnitModelOut

logger = getLogger(__name__)


async def create_department_unit(department_id: int, model: DepartmentUnitModelIn, db: Session):
    department = await get_department_by_id(department_id, db)
    if not department:
        raise NoDataFoundException(f"Department with ID {department_id} not found")

    # CHANGED — now also stores the unit's email
    unit = DepartmentUnit(department_id=department_id, name=model.name, email=model.email)
    unit_db = await save_department_unit(unit, db)
    return DepartmentUnitModelOut.model_validate(unit_db)


async def list_department_units(department_id: int, db: Session):
    units = await get_units_by_department(department_id, db)
    return [DepartmentUnitModelOut.model_validate(u) for u in units]


async def update_department_unit_info(unit_id: int, model: DepartmentUnitModelIn, db: Session):
    unit_db = await get_department_unit_by_id(unit_id, db)
    if not unit_db:
        raise NoDataFoundException(f"Department unit with ID {unit_id} not found")

    unit_db.name = model.name
    unit_db.email = model.email  # NEW
    updated = await update_department_unit(unit_db, db)
    return DepartmentUnitModelOut.model_validate(updated)


async def delete_department_unit_info(unit_id: int, db: Session):
    unit_db = await get_department_unit_by_id(unit_id, db)
    if not unit_db:
        raise NoDataFoundException(f"Department unit with ID {unit_id} not found")

    unit_db.is_active = False
    updated = await update_department_unit(unit_db, db)
    return DepartmentUnitModelOut.model_validate(updated)