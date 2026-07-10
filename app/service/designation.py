from logging import getLogger

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from crud.designation import save_designation, get_designation_by_id, get_designations, \
    update_designation, delete_designation, get_designation_by_name
from db.models.models import Designation
from exception.exception import NoDataFoundException, ValidationException
from models.designation import DesignationModelIn, DesignationModelUpdate, DesignationModelOut

logger = getLogger(__name__)


async def create_designation(designation_model: DesignationModelIn, db: Session):
    logger.info("Create designation process started")

    existing = await get_designation_by_name(designation_model.name, db)
    if existing:
        raise ValidationException(f"Designation '{designation_model.name}' already exists")

    designation = Designation(
        name=designation_model.name,
        description=designation_model.description,
    )
    designation_db = await save_designation(designation, db)

    logger.info("Create designation process ended")
    return DesignationModelOut.model_validate(designation_db)


async def get_designation_list_service(db: Session):
    logger.info("Get designation list process started")

    designations = await get_designations(db)
    result = [DesignationModelOut.model_validate(d) for d in designations]

    logger.info("Get designation list process ended")
    return result


async def update_designation_info(designation_id: int, designation_model: DesignationModelUpdate, db: Session):
    logger.info(f"Update designation {designation_id} process started")

    designation_db = await get_designation_by_id(designation_id, db)
    if not designation_db:
        raise NoDataFoundException(f"Designation {designation_id} not found")

    if designation_db.name != designation_model.name:
        clash = await get_designation_by_name(designation_model.name, db)
        if clash and clash.id != designation_id:
            raise ValidationException(f"Designation '{designation_model.name}' already exists")

    designation_db.name = designation_model.name
    designation_db.description = designation_model.description
    designation_db.is_active = designation_model.is_active

    updated = await update_designation(designation_db, db)

    logger.info(f"Update designation {designation_id} process ended")
    return DesignationModelOut.model_validate(updated)


async def delete_designation_info(designation_id: int, db: Session):
    logger.info(f"Delete designation {designation_id} process started")

    designation_db = await get_designation_by_id(designation_id, db)
    if not designation_db:
        raise NoDataFoundException(f"Designation {designation_id} not found")

    try:
        await delete_designation(designation_db, db)
    except IntegrityError:
        db.rollback()
        logger.warning(f"Delete blocked by foreign key constraint for designation {designation_id}")
        raise ValidationException(
            "This designation can't be deleted because it's still assigned to one or more users. "
            "Reassign those users first, or deactivate the designation instead."
        )

    logger.info(f"Delete designation {designation_id} process ended")