import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL")
    EMAIL_API_KEY = os.getenv("EMAIL_API_KEY")

    OTP_EXPIRY = 300  # 5 minutes
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@example.com")

settings = Settings()
