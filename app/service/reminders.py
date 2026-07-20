from datetime import datetime, timedelta
from logging import getLogger

from sqlalchemy.orm import Session

from config.config import PENDING_REMINDER_DAYS, REMINDER_RESEND_INTERVAL_DAYS
from db.models.models import Letter
from utils.email import send_email
from utils.email_templates import letter_pending_reminder_email

logger = getLogger(__name__)


async def send_pending_letter_reminders(db: Session):
    logger.info("Pending-letter reminder sweep started")
    stale_cutoff = datetime.utcnow() - timedelta(days=PENDING_REMINDER_DAYS)
    resend_cutoff = datetime.utcnow() - timedelta(days=REMINDER_RESEND_INTERVAL_DAYS)

    letters = (
        db.query(Letter)
        .filter(Letter.is_active, Letter.status_since <= stale_cutoff)
        .all()
    )

    for letter in letters:
        if letter.last_reminder_sent and letter.last_reminder_sent > resend_cutoff:
            continue  # already reminded recently

        days = (datetime.utcnow() - letter.status_since).days
        status_name = letter.status.name if letter.status else "Unknown"

        sent_any = False
        for la in letter.assignees:
            if la.assignee and la.assignee.email:
                subject, body = letter_pending_reminder_email(letter.code, letter.subject or "", status_name, days)
                ok = await send_email(la.assignee.email, subject, body)
                sent_any = sent_any or ok

        if sent_any:
            letter.last_reminder_sent = datetime.utcnow()
            db.commit()

    logger.info(f"Pending-letter reminder sweep finished — checked {len(letters)} letters")