# app/email_utils.py
import aiosmtplib
from email.mime.text import MIMEText
import smtplib
from email.message import EmailMessage
from app.config import settings

def send_email(to_email, subject, body):
    msg = EmailMessage()
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(settings.EMAIL_FROM, settings.EMAIL_API_KEY)
        smtp.send_message(msg)


async def send_email_async(to_email: str, subject: str, message: str):
    msg = MIMEText(message)
    msg["From"] = settings.FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        start_tls=True,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
    )
