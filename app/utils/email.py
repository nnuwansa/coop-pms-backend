import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from logging import getLogger

from config.config import (
    SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD,
    SMTP_FROM_EMAIL, SMTP_FROM_NAME,
)

logger = getLogger(__name__)


def _send_email_sync(to_email: str, subject: str, body_html: str) -> None:
    """Blocking SMTP send — must be run off the event loop."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    msg["To"] = to_email
    msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM_EMAIL, [to_email], msg.as_string())


async def send_email(to_email: str, subject: str, body_html: str) -> bool:
    """
    Sends an email without blocking the event loop.
    Returns True on success, False on failure — never raises, so a failed
    email never breaks the caller's main workflow (e.g. letter creation).
    """
    try:
        await asyncio.to_thread(_send_email_sync, to_email, subject, body_html)
        logger.info(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False