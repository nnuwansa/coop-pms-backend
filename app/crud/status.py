from logging import getLogger

from sqlalchemy.orm import Session

from db.models.models import Status

logger = getLogger(__name__)


async def save_status(status: Status, db: Session):
    db.add(status)
    db.commit()
    db.refresh(status)
    return status


async def get_status_by_id(status_id: int, db: Session):
    return db.query(Status).filter(Status.id == status_id).first()


async def get_all_statuses(db: Session):
    return db.query(Status).filter(Status.is_active).all()


async def update_status(status: dict, db: Session):
    db.commit()
    db.refresh(status)
    return status
