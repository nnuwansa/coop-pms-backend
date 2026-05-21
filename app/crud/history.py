from sqlalchemy.orm import Session

from db.models.models import History


async def save_history(history: History, db: Session) -> History:
    db.add(history)
    db.commit()
    db.refresh(history)
    return history
