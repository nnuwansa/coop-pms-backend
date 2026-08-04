from logging import getLogger
from sqlalchemy.orm import Session
from db.models.models import LetterAssigneeStatus

logger = getLogger(__name__)


async def get_assignee_statuses_by_letter(letter_id: int, db: Session):
    return db.query(LetterAssigneeStatus).filter(LetterAssigneeStatus.letter_id == letter_id).all()


async def get_assignee_status(letter_id: int, assignee_id: int, db: Session):
    return db.query(LetterAssigneeStatus).filter(
        LetterAssigneeStatus.letter_id == letter_id,
        LetterAssigneeStatus.assignee_id == assignee_id,
    ).first()


async def create_assignee_status(row: LetterAssigneeStatus, db: Session):
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


async def delete_assignee_status(letter_id: int, assignee_id: int, db: Session):
    db.query(LetterAssigneeStatus).filter(
        LetterAssigneeStatus.letter_id == letter_id,
        LetterAssigneeStatus.assignee_id == assignee_id,
    ).delete()