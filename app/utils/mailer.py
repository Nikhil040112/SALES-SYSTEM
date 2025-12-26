import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    MAIL_FROM
)


def send_email(to_email: str, subject: str, html_content: str):
    """
    Generic email sender used by scheduler jobs.
    """

    msg = MIMEMultipart("alternative")
    msg["From"] = MAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

    except Exception as e:
        # Intentionally not raising error
        # Scheduler should never crash due to email failure
        print(f"[MAIL ERROR] Failed to send email to {to_email}: {e}")