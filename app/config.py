import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL")
    EMAIL_FROM = os.getenv("EMAIL_FROM")
    EMAIL_API_KEY = os.getenv("EMAIL_API_KEY")

settings = Settings()
