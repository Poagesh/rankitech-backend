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
