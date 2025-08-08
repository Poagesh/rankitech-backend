from celery import Celery
from app.config import settings
from app.database import SessionLocal
from app import models, nlp_utils, email_utils
from .email_utils import send_email_async
import asyncio

celery = Celery("tasks", broker=settings.REDIS_BROKER_URL, backend=settings.REDIS_BROKER_URL)

celery.conf.beat_schedule = {
    'send-job-matching-emails-every-hour': {
        'task': 'app.tasks.matching_email_task',
        'schedule': 3600.0  # every hour
    }
}

# @celery.task
# def process_matching(jd_id, email):
#     db = SessionLocal()
#     jd = db.query(models.JobDescription).get(jd_id)
#     profiles = db.query(models.ConsultantProfile).all()
    
#     results = nlp_utils.compute_similarity(jd.content, profiles)
#     top3 = results[:3]

#     for pid, score in top3:
#         db.add(models.MatchResult(jd_id=jd_id, profile_id=pid, similarity_score=score))
#     db.commit()

#     if top3:
#         body = "\n".join([f"Profile ID: {pid}, Score: {score:.2f}" for pid, score in top3])
#         email_utils.send_email(email, "Top Matches for JD", body)
#     else:
#         email_utils.send_email(email, "No Matches Found", "We couldn't find a suitable profile.")

@celery.task(name="send_email_task")
def send_email_task(to_email: str, subject: str, message: str):
    try:
        asyncio.run(send_email_async(to_email, subject, message))
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

@celery.task(name="app.tasks.matching_email_task")
def matching_email_task():
    from app.matching_notifier import process_expired_jobs_and_send_emails
    process_expired_jobs_and_send_emails()
