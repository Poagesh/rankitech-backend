# app/email_utils.py
import aiosmtplib
from email.mime.text import MIMEText
from email.message import EmailMessage
import smtplib
from app.config import settings

def send_email(to_email: str, subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_API_PORT) as smtp:
            smtp.starttls()
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Sync email error: {e}")


async def send_email_async(to_email: str, subject: str, message: str):
    msg = MIMEText(message)
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_API_PORT,
            start_tls=True,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
        )
    except Exception as e:
        print(f"Async email error: {e}")
