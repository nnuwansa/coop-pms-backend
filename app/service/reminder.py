from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from db.models.models import LetterAssigneeStatus, Status
from utils.email import send_email
from utils.email_templates import letter_pending_reminder_email
import logging

logger = logging.getLogger(__name__)

PENDING_REMINDER_DAYS = 3   # configurable threshold


async def send_pending_letter_reminders(db: Session) -> None:
    """
    Runs daily (via the existing apscheduler job). Finds every assignee
    status row that:
      - is NOT already "Completed"
      - has been sitting in its current status for >= PENDING_REMINDER_DAYS
      - hasn't already had a reminder sent for THIS status period
    and emails the assignee a reminder. reminder_sent is flipped to True so
    the same pending status never triggers a second email — it only resets
    (see update_assignee_status) if the assignee actually changes status.
    """
    cutoff = datetime.utcnow() - timedelta(days=PENDING_REMINDER_DAYS)

    stale_rows = (
        db.query(LetterAssigneeStatus)
        .join(Status, Status.id == LetterAssigneeStatus.status_id)
        .filter(
            Status.name != "Completed",
            LetterAssigneeStatus.status_since <= cutoff,
            LetterAssigneeStatus.reminder_sent == False,
        )
        .all()
    )

    logger.info(f"Pending-letter reminder check: {len(stale_rows)} stale assignee status row(s) found")

    for row in stale_rows:
        try:
            assignee = row.assignee
            letter = row.letter
            status = row.status
            if not assignee or not assignee.email or not letter:
                continue

            days_pending = (datetime.utcnow() - row.status_since).days

            email_subject, email_body = letter_pending_reminder_email(
                               letter_code = letter.code,
                           subject = letter.subject or "",
                           status_name = status.name if status else "Pending",
                           days = days_pending,
                       )
            await send_email(assignee.email, email_subject, email_body)

            row.reminder_sent = True   # mark so this same stale period doesn't email again tomorrow
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to send pending reminder for letter_assignee_status {row.id}: {e}")
            db.rollback()