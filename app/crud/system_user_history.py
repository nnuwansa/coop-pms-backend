from logging import getLogger
from typing import Optional

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from db.models.models import SystemUserHistory

logger = getLogger(__name__)


async def save_user_history(
        user_id: int,
        action: str,
        description: str,
        performed_by: Optional[str],
        db: Session
):
    history = SystemUserHistory(
        user_id=user_id,
        action=action,
        description=description,
        performed_by=performed_by,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


async def get_user_history(user_id: int, db: Session):
    stmt = (
        select(SystemUserHistory)
        .where(SystemUserHistory.user_id == user_id)
        .order_by(desc(SystemUserHistory.create_datetime))
    )
    result = db.execute(stmt)
    return result.scalars().all()