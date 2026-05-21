from logging import getLogger

from sqlalchemy.orm import Session

from crud.status import get_status_by_id, save_status, get_all_statuses, update_status
from db.models.models import Status
from exception.exception import NoDataFoundException
from models.status import StatusModelIn, StatusModelOut

logger = getLogger(__name__)


async def create_status(status_model: StatusModelIn, db: Session):
    logger.info("Create status process started")

    status = Status(name=status_model.name)

    status_db = await save_status(status, db)
    status_response = StatusModelOut.model_validate(status_db)

    logger.info("Create status process ended")
    return status_response


async def get_all_active_statuses_service(db: Session):
    logger.info("Get all active statuses process started")

    statuses = await get_all_statuses(db)

    status_list = [
        StatusModelOut.model_validate(status) for status in statuses
    ]

    logger.info("Get all active statuses process ended")
    return status_list


async def update_status_id(status_id: int, status_model: StatusModelIn, db: Session):
    logger.info(f"Update status process started for status ID {status_id}")

    status_db = await get_status_by_id(status_id, db)
    if not status_db:
        raise NoDataFoundException(f"Status with ID {status_id} not found for update")

    update_data = status_model.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(status_db, field, value)

    status_db = await update_status(status_db, db)
    status_response = StatusModelOut.model_validate(status_db)
    logger.info(f"Update status process ended for status ID {status_id}")
    return status_response


async def delete_status(status_id: int, db: Session):
    logger.info(f"Delete status process started for status ID {status_id}")

    status_db = await get_status_by_id(status_id, db)
    if not status_db:
        raise NoDataFoundException(f"Status with ID {status_id} not found for delete")

    status_db.is_active = False
    status_db = await save_status(status_db, db)
    status_response = StatusModelOut.model_validate(status_db)
    logger.info(f"Delete status process ended for status ID {status_id}")
    return status_response
