from datetime import datetime


def letter_received_email(
        organization_name: str,
        letter_code: str,
        subject: str,
        received_datetime: datetime,
) -> tuple[str, str]:
    """Returns (email_subject, html_body) for a 'letter received' notification."""

    email_subject = f"Letter Received — {letter_code}"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1e293b;">Letter Received Confirmation</h2>
        <p>Dear {organization_name},</p>
        <p>
            This is to confirm that a letter sent on behalf of <strong>{organization_name}</strong>
            has been received and recorded in our system.
        </p>
        <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
            <tr>
                <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold; background: #f8fafc;">Letter Code</td>
                <td style="padding: 8px; border: 1px solid #e2e8f0;">{letter_code}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold; background: #f8fafc;">Subject</td>
                <td style="padding: 8px; border: 1px solid #e2e8f0;">{subject}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold; background: #f8fafc;">System Added Date/Time</td>
                <td style="padding: 8px; border: 1px solid #e2e8f0;">{received_datetime.strftime('%d %B %Y, %I:%M %p')}</td>
            </tr>
        </table>
        <p>Please quote the letter code above in any future correspondence regarding this matter.</p>
        <p style="margin-top: 24px; color: #64748b; font-size: 13px;">
            This is an automated notification from the COOP Postal Management System.
            Please do not reply directly to this email.
        </p>
    </div>
    """

    return email_subject, html_body


def letter_pending_reminder_email(letter_code: str, subject: str, status_name: str, days: int) -> tuple[str, str]:
    email_subject = f"Reminder: Letter {letter_code} pending action ({days} days)"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #b45309;">Action Needed</h2>
        <p>
            The letter below has been in status <strong>{status_name}</strong> for
            <strong>{days} day{'s' if days != 1 else ''}</strong> without any action taken.
        </p>
        <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
            <tr>
                <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold; background: #f8fafc;">Letter Code</td>
                <td style="padding: 8px; border: 1px solid #e2e8f0;">{letter_code}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold; background: #f8fafc;">Subject</td>
                <td style="padding: 8px; border: 1px solid #e2e8f0;">{subject}</td>
            </tr>
        </table>
        <p>Please log in to COOP PMS and take the required action on this letter.</p>
    </div>
    """
    return email_subject, html_body