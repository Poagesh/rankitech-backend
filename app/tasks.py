from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Job, JobApplication, RankedApplicantMatch, ConsultantProfile, Resume, recruiter
from app.resume_matcher import ResumeJDMatcher, JobDescription
import tempfile
import os
from celery import Celery
from app.config import settings
from app.database import SessionLocal
from app import models, nlp_utils, email_utils
from .email_utils import send_email_async
import asyncio
from celery.schedules import crontab

celery = Celery("tasks", broker=settings.REDIS_BROKER_URL, backend=settings.REDIS_BROKER_URL)

celery.conf.beat_schedule = {
    'process-expired-jobs': {
        'task': 'app.tasks.check_expired_jobs',
        'schedule': crontab(minute='*/15'),  # Check every 15 minutes
    },
}
celery.conf.timezone = 'UTC'

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


# In tasks.py

@celery.task
def check_expired_jobs():
    """Check for jobs past deadline and process them automatically"""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        expired_jobs = db.query(Job).filter(
            Job.deadline_to_apply <= now,
            Job.email_sent == False,      # Not processed yet
            Job.status == "active"        # Still active
        ).all()
        
        print(f"Found {len(expired_jobs)} expired jobs to process")
        
        for job in expired_jobs:
            print(f"Processing expired job: {job.job_title} (ID: {job.id})")
            process_expired_job.delay(job.id)
            
    except Exception as e:
        print(f"Error checking expired jobs: {e}")
    finally:
        db.close()

@celery.task
def process_expired_job(job_id: int):
    """Process a specific expired job: run AI matching and send emails"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return f"Job {job_id} not found"

        if job.email_sent or job.status != "active":
            return f"Job {job_id} already processed"
        
        print(f"Starting AI processing for job: {job.job_title}")
        
        # Get all applicants
        applications = db.query(JobApplication).filter(JobApplication.job_id == job_id).all()
        if not applications:
            job.status = "closed"
            job.email_sent = True  # Mark as processed
            db.commit()
            return f"No applicants found for job {job_id}"
        
        print(f"Found {len(applications)} applicants to process")
        
        # Run AI matching
        top_candidates = run_ai_matching(db, job, applications)
        
        if not top_candidates:
            job.status = "closed"
            job.email_sent = True
            db.commit()
            return f"No valid candidates after AI processing for job {job_id}"
        
        # Send emails to top N candidates
        selected_count = min(len(top_candidates), job.max_candidates)
        selected_candidates = top_candidates[:selected_count]
        
        print(f"Sending emails to top {selected_count} candidates")
        
        for candidate in selected_candidates:
            send_selection_email.delay(
                candidate['consultant_id'],
                candidate['name'],
                candidate['email'],
                job.job_title,
                job.id,
                candidate['match_score'],
                candidate['skills_matched']
            )
        
        # Mark job as processed
        job.email_sent = True
        job.status = "processed"
        db.commit()
        
        print(f"Successfully processed job {job_id}, sent emails to {selected_count} candidates")
        return f"Processed job {job_id}, selected {selected_count}/{len(applications)} candidates"
        
    except Exception as e:
        print(f"Error processing job {job_id}: {e}")
        # Don't mark as processed if there was an error
        return f"Error processing job {job_id}: {str(e)}"
    finally:
        db.close()

def run_ai_matching(db: Session, job: Job, applications):
    """Run AI matching for all applicants"""
    recruiter_obj = db.query(recruiter).filter(recruiter.id == job.recruiter_id).first()
    
    job_input = JobDescription(
        title=job.job_title,
        company=recruiter_obj.company_name if recruiter_obj else "Company",
        description=job.job_description or "",
        required_skills=job.required_skills or [],
        preferred_skills=job.preferred_skills or [],
        experience_level=job.experience_level or "Any",
        location=job.location or "Remote"
    )
    
    matcher = ResumeJDMatcher(model="gemma3:1b")
    candidates = []
    
    # Clear old matches
    db.query(RankedApplicantMatch).filter(RankedApplicantMatch.job_id == job.id).delete()
    
    for application in applications:
        consultant = db.query(ConsultantProfile).filter(
            ConsultantProfile.id == application.consultant_id
        ).first()
        
        resume = db.query(Resume).filter(
            Resume.consultant_id == application.consultant_id
        ).order_by(Resume.uploaded_at.desc()).first()
        
        if not consultant or not resume or not resume.file_data:
            continue
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(resume.file_data)
            tmp_file_path = tmp_file.name
        
        try:
            result = matcher.match_resume_to_job(tmp_file_path, job_input)
            resume_data = matcher.process_resume(tmp_file_path)
            report = matcher.generate_report(result, resume_data, job_input)
            
            # Save to database
            db_match = RankedApplicantMatch(
                job_id=job.id,
                consultant_id=consultant.id,
                match_score=float(result.overall_score),
                top_skills_matched=result.matching_skills,
                missing_skills=result.missing_skills,
                report=report,
                created_at=datetime.utcnow()
            )
            db.add(db_match)
            
            candidates.append({
                'consultant_id': consultant.id,
                'name': consultant.name,
                'email': consultant.primary_email,
                'match_score': result.overall_score,
                'skills_matched': ', '.join(result.matching_skills[:3]),  # Top 3 skills
                'report': report
            })
            
        except Exception as e:
            print(f"Error processing consultant {consultant.id}: {e}")
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    
    db.commit()
    candidates.sort(key=lambda x: x['match_score'], reverse=True)
    return candidates

@celery.task
def send_selection_email(consultant_id: int, name: str, email: str, job_title: str, job_id: int, match_score: float, skills_matched: str):
    """Send congratulations email to selected candidate"""
    subject = f"🎉 Congratulations! You've been shortlisted for {job_title}"
    
    message = f"""
Dear {name},

🎉 Excellent news! You've been selected as one of the top candidates for:

📋 Position: {job_title}
🎯 Your AI Match Score: {match_score:.1f}%
⭐ Key Skills Matched: {skills_matched}

Our advanced AI matching system analyzed all applications and identified you as an exceptional fit for this role based on your skills, experience, and qualifications.

🚀 What happens next?
• Our hiring team will review your profile in detail
• You may receive a call/email for the next round within 2-3 business days  
• Please keep your phone and email accessible
• Prepare for potential interviews

💡 Pro tip: Review the job requirements and prepare examples showcasing your relevant experience!

Thank you for applying, and congratulations on making it to the shortlist!

Best regards,
The Hiring Team

---
This is an automated message from our AI-powered recruitment system.
Job ID: {job_id} | Your Candidate ID: {consultant_id}
Match Score: {match_score:.1f}%
    """.strip()
    
    # Use your existing email task
    send_email_task.delay(email, subject, message)
    return f"Selection email sent to {name}"
