from app.database import SessionLocal
from app.models import Job, RankedApplicantMatch
from datetime import datetime
from app.tasks import send_email_task

def process_expired_jobs_and_send_emails():
    db = SessionLocal()
    try:
        jobs = db.query(Job).filter(Job.deadline_to_apply < datetime.utcnow(), Job.email_sent == False).all()
        for job in jobs:
            matches = (
                db.query(RankedApplicantMatch)
                .filter(RankedApplicantMatch.job_id == job.id)
                .order_by(RankedApplicantMatch.match_score.desc())
                .limit(5)
                .all()
            )

            for match in matches:
                message = f"You've been selected as a top match for the job: {job.job_title}."
                send_email_task.delay(match.consultant.primary_email, f"Top Job Match - {job.job_title}", message)

            job.email_sent = True
            db.commit()
    finally:
        db.close()
