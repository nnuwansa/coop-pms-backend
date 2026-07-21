# from datetime import datetime
#
#
# def letter_received_email(
#         organization_name: str,
#         letter_code: str,
#         subject: str,
#         received_datetime: datetime,
# ) -> tuple[str, str]:
#     """Returns (email_subject, html_body) for a 'letter received' notification."""
#
#     email_subject = f"Letter Received — {letter_code}"
#
#     html_body = f"""
#     <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
#         <h2 style="color: #1e293b;">Letter Received Confirmation</h2>
#         <p>Dear {organization_name},</p>
#         <p>
#             This is to confirm that a letter sent on behalf of <strong>{organization_name}</strong>
#             has been received and recorded in our system.
#         </p>
#         <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
#             <tr>
#                 <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold; background: #f8fafc;">Letter Code</td>
#                 <td style="padding: 8px; border: 1px solid #e2e8f0;">{letter_code}</td>
#             </tr>
#             <tr>
#                 <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold; background: #f8fafc;">Subject</td>
#                 <td style="padding: 8px; border: 1px solid #e2e8f0;">{subject}</td>
#             </tr>
#
#         </table>
#         <p>Please quote the letter code above in any future correspondence regarding this matter.</p>
#         <p style="margin-top: 24px; color: #64748b; font-size: 13px;">
#             This is an automated notification from the COOP Postal Management System.
#             Please do not reply directly to this email.
#         </p>
#     </div>
#     """
#
#     return email_subject, html_body
#
#
# def letter_pending_reminder_email(letter_code: str, subject: str, status_name: str, days: int) -> tuple[str, str]:
#     email_subject = f"Reminder: Letter {letter_code} pending action ({days} days)"
#     html_body = f"""
#     <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
#         <h2 style="color: #b45309;">Action Needed</h2>
#         <p>
#             The letter below has been in status <strong>{status_name}</strong> for
#             <strong>{days} day{'s' if days != 1 else ''}</strong> without any action taken.
#         </p>
#         <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
#             <tr>
#                 <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold; background: #f8fafc;">Letter Code</td>
#                 <td style="padding: 8px; border: 1px solid #e2e8f0;">{letter_code}</td>
#             </tr>
#             <tr>
#                 <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold; background: #f8fafc;">Subject</td>
#                 <td style="padding: 8px; border: 1px solid #e2e8f0;">{subject}</td>
#             </tr>
#         </table>
#         <p>Please log in to COOP PMS and take the required action on this letter.</p>
#     </div>
#     """
#     return email_subject, html_body

from datetime import datetime


def letter_received_email(
        organization_name: str,
        letter_code: str,
        subject: str,
        received_datetime: datetime,
) -> tuple[str, str]:
    """Returns (email_subject, html_body) for a 'letter received' notification."""

    email_subject = f"Letter Received Confirmation — {letter_code}"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h3 style="color: #1e293b;">ලිපිය ලැබීම තහවුරු කිරීම</h3>
        <p>ගරු මහත්මයාණනි/මහත්මියනි,</p>
        <p>
            <strong>{organization_name}</strong> විසින් අප වෙත එවන ලද ලිපිය
            ලැබී, ලේඛනගත කර ඇති බව මෙයින් තහවුරු කරමු.
        </p>
        <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
            <tr>
                <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold; background: #f8fafc;">ලිපි කේතය</td>
                <td style="padding: 8px; border: 1px solid #e2e8f0;">{letter_code}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold; background: #f8fafc;">විෂය</td>
                <td style="padding: 8px; border: 1px solid #e2e8f0;">{subject}</td>
            </tr>
        </table>
        <p>මෙම කරුණ සම්බන්ධයෙන් ඉදිරියේදී ඇතිවන සියලුම ලිපි ගනුදෙනුවලදී කරුණාකර ඉහත ලිපි කේතය සඳහන් කරන්න.</p>

        <p style="margin-top: 24px; margin-bottom: 4px;">
            <strong>සමුපකාර සංවර්ධන දෙපාර්තමේන්තුව</strong><br/>
            මහනුවර
        </p>

        <p style="margin-top: 16px; color: #64748b; font-size: 12px;">
            This is an automated notification from the COOP Postal Management System.
            Please do not reply directly to this email.
        </p>
    </div>
    """

    return email_subject, html_body


def letter_pending_reminder_email(letter_code: str, subject: str, status_name: str, days: int) -> tuple[str, str]:
    email_subject = f"මතක් කිරීම: ලිපිය {letter_code} ක්‍රියාමාර්ගයක් අපේක්ෂාවෙන් ඇත ({days} දින)"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #b45309;">ක්‍රියාමාර්ගයක් අවශ්‍යයි</h2>
        <p>
            පහත සඳහන් ලිපිය <strong>{status_name}</strong> තත්ත්වයේ
            <strong>දින {days}ක්</strong> කිසිදු ක්‍රියාමාර්ගයක් නොගෙන පවතී.
        </p>
        <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
            <tr>
                <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold; background: #f8fafc;">ලිපි කේතය</td>
                <td style="padding: 8px; border: 1px solid #e2e8f0;">{letter_code}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold; background: #f8fafc;">විෂය</td>
                <td style="padding: 8px; border: 1px solid #e2e8f0;">{subject}</td>
            </tr>
        </table>
        <p>කරුණාකර COOP PMS පද්ධතියට පිවිස මෙම ලිපිය සම්බන්ධයෙන් අවශ්‍ය ක්‍රියාමාර්ගය ගන්න.</p>
    </div>
    """
    return email_subject, html_body