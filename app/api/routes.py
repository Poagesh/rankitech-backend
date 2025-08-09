# app/api/routes.py
import random
import json
import os
import tempfile
from io import BytesIO
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Header
from fastapi.security import OAuth2PasswordBearer
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.auth import create_access_token, verify_access_token
from app import models, schemas, tasks
from app.database import SessionLocal
from app.models import ConsultantProfile, EducationDetail, Project, TechnicalSkill, Language, Subject, Experience, Achievement, ExtraCurricular, Resume, Job, JobApplication, recruiter, RankedApplicantMatch, admin
from app.schemas import ProfileInput, ProfileResponse, EmailRequest, OTPVerifyRequest, JobCreate, JobResponse, JobApplicationCreate, JobApplicationResponse, RankApplicantsRequest, ApplicantRankedMatch, AdminCreate, AdminUpdate, AdminResponse, RecruiterResponse, RecruiterUpdate
from app.tasks import send_email_task
from app.redis_manager import get_redis
from app.config import settings
from app.crud import create_recruiter
from app.resume_matcher import ResumeJDMatcher, JobDescription
from passlib.context import CryptContext
from passlib.hash import bcrypt




router = APIRouter()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/jd/")
def add_jd(jd: schemas.JDInput, email: str, db: Session = Depends(get_db)):
    new_jd = models.JobDescription(**jd.dict())
    db.add(new_jd)
    db.commit()
    db.refresh(new_jd)
    tasks.process_matching.delay(new_jd.id, email)
    return {"msg": "JD added and processing started"}

#-------------Recruiter Registration-------------
@router.post("/register-recruiter", response_model=schemas.RecruiterCreate)
def register_recruiter(recruiter: schemas.RecruiterCreate, db: Session = Depends(get_db)):
    return create_recruiter(db, recruiter)

def get_recruiters(db: Session, skip: int = 0, limit: int = 10):
    return db.query(recruiter).offset(skip).limit(limit).all()

def get_recruiter(db: Session, recruiter_id: int):
    return db.query(recruiter).filter(recruiter.id == recruiter_id).first()

def update_recruiter(db: Session, recruiter_id: int, recruiter_update: RecruiterUpdate):
    db_recruiter = get_recruiter(db, recruiter_id)
    if db_recruiter is None:
        return None
    
    update_data = recruiter_update.dict(exclude_unset=True)
    if 'password' in update_data:
        hashed_password = bcrypt.hash(recruiter_update.password)
        update_data['password'] = hashed_password
    
    for key, value in update_data.items():
        setattr(db_recruiter, key, value)
    
    try:
        db.commit()
        db.refresh(db_recruiter)
        return db_recruiter
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

def delete_recruiter(db: Session, recruiter_id: int):
    db_recruiter = get_recruiter(db, recruiter_id)
    if db_recruiter is None:
        return None
    db.delete(db_recruiter)
    db.commit()
    return db_recruiter

# Endpoints (GET, GET by ID, PUT, DELETE)
@router.get("/recruiters", response_model=List[RecruiterResponse])
def read_recruiters(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    recruiters = get_recruiters(db, skip=skip, limit=limit)
    return recruiters

@router.get("/get-recruiter/{recruiter_id}", response_model=RecruiterResponse)
def read_recruiter(recruiter_id: int, db: Session = Depends(get_db)):
    recruiter = get_recruiter(db, recruiter_id)
    if recruiter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter not found")
    return recruiter

@router.put("/put-recruiter/{recruiter_id}", response_model=RecruiterResponse)
def update_recruiter_endpoint(recruiter_id: int, recruiter_update: RecruiterUpdate, db: Session = Depends(get_db)):
    updated_recruiter = update_recruiter(db, recruiter_id, recruiter_update)
    if updated_recruiter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter not found")
    return updated_recruiter

@router.delete("/delete-recruiter/{recruiter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recruiter_endpoint(recruiter_id: int, db: Session = Depends(get_db)):
    deleted_recruiter = delete_recruiter(db, recruiter_id)
    if deleted_recruiter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter not found")
    return None
#-------------Admin Registration-------------

@router.get("/readadmins", response_model=List[AdminResponse])
def read_admins(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    admins = db.query(models.admin).offset(skip).limit(limit).all()
    return admins

@router.get("/readadmin/{admin_id}", response_model=AdminResponse)
def read_admin(admin_id: int, db: Session = Depends(get_db)):
    admin = db.query(models.admin).filter(models.admin.id == admin_id).first()
    if admin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    return admin

@router.post("/createAdmin")
def create_admin(admin_data: schemas.AdminCreate, db: Session = Depends(get_db)):
    existing_admin = db.query(models.admin).filter(models.admin.email == admin_data.email).first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin with this email already exists")

    hashed_password = bcrypt.hash(admin_data.password)

    new_admin = models.admin(
        name=admin_data.name,
        email=admin_data.email,
        password=hashed_password
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return {"id": new_admin.id, "name": new_admin.name, "email": new_admin.email}


@router.put("/update-admin/{admin_id}", response_model=AdminResponse)
def update_admin(admin_id: int, admin_update: AdminUpdate, db: Session = Depends(get_db)):
    admin = db.query(models.admin).filter(models.admin.id == admin_id).first()
    if admin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")

    hashed_password = bcrypt.hash(admin_update.password)
    admin.password = hashed_password

    update_data = admin_update.dict(exclude_unset=True)
    if 'password' in update_data:
        # In production, hash the new password
        # update_data['password'] = hashpw(update_data['password'].encode('utf-8'), gensalt())
        pass  # For now, plain as per model
    
    for key, value in update_data.items():
        setattr(admin, key, value)
    
    try:
        db.commit()
        db.refresh(admin)
        return admin
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
    
@router.delete("/delete-admin/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin(admin_id: int, db: Session = Depends(get_db)):
    admin = db.query(models.admin).filter(models.admin.id == admin_id).first()
    if admin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    db.delete(admin)
    db.commit()
    return None


# @router.post("/ar/register", response_model=ProfileResponse)
# def register_consultant_profile(profile_in: ProfileInput, db: Session = Depends(get_db)):
#     # Check if primary_email already exists
#     existing_profile = db.query(ConsultantProfile).filter(ConsultantProfile.primary_email == profile_in.primary_email).first()
#     if existing_profile:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="A profile with this primary email already exists."
#         )

#     profile = create_consultant_profile(db, profile_in)
#     return profile

# ---------- Create Profile ----------


@router.post("/ar-register", response_model=ProfileResponse)
async def create_profile(
    name: str = Form(...),
    dob: str = Form(...),
    gender: str = Form(...),
    college: str = Form(...),
    institution_roll_no: str = Form(...),
    primary_email: str = Form(...),
    personal_email: Optional[str] = Form(None),
    mobile_no: str = Form(...),
    password: str = Form(...),
    country: str = Form(...),
    pincode: str = Form(...),
    state: str = Form(...),
    district: str = Form(...),
    city: str = Form(...),
    address_line: str = Form(...),
    # resume: UploadFile = File(...),
    education_details: str = Form("[]"),
    projects: str = Form("[]"),
    technical_skills: str = Form("[]"),
    languages: str = Form("[]"),
    subjects: str = Form("[]"),
    experiences: str = Form("[]"),
    achievements: str = Form("[]"),
    extra_curricular_activities: str = Form("[]"),
    db: Session = Depends(get_db)
):
    # Convert DOB string to date object
    try:
        dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    # Parse JSON strings
    education_details_list = json.loads(education_details)
    projects_list = json.loads(projects)
    technical_skills_list = json.loads(technical_skills)
    languages_list = json.loads(languages)
    subjects_list = json.loads(subjects)
    experiences_list = json.loads(experiences)
    achievements_list = json.loads(achievements)
    extra_curricular_activities_list = json.loads(extra_curricular_activities)

    # Check if email exists
    existing = db.query(ConsultantProfile).filter(ConsultantProfile.primary_email == primary_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    hashed_password = pwd_context.hash(password)

    # Read resume bytes
    # resume_bytes = await resume.read()

    # Create main profile
    profile = ConsultantProfile(
        name=name,
        dob=dob_date,
        gender=gender,
        college=college,
        institution_roll_no=institution_roll_no,
        primary_email=primary_email,
        personal_email=personal_email,
        mobile_no=mobile_no,
        password=hashed_password,
        country=country,
        pincode=pincode,
        state=state,
        district=district,
        city=city,
        address_line=address_line,
        # resume=resume_bytes
    )

    # Create nested relationships
    profile.education_details = [EducationDetail(**ed) for ed in education_details_list]
    profile.projects = [Project(**p) for p in projects_list]
    profile.technical_skills = [TechnicalSkill(**s) for s in technical_skills_list]
    profile.languages = [Language(**l) for l in languages_list]
    profile.subjects = [Subject(**sub) for sub in subjects_list]
    profile.experiences = [Experience(**e) for e in experiences_list]
    profile.achievements = [Achievement(**a) for a in achievements_list]
    profile.extra_curricular_activities = [ExtraCurricular(**ec) for ec in extra_curricular_activities_list]

    # Save to DB
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile

#-------------OTP Generation and Email Sending-------------
@router.post("/send-otp")
async def send_otp(data: EmailRequest):
    redis = await get_redis()
    otp = str(random.randint(100000, 999999))
    await redis.setex(f"otp:{data.email}", settings.OTP_EXPIRY, otp)

    # Send email via Celery
    send_email_task.delay(
        data.email,
        "Your OTP Code",
        f"Your OTP code is {otp}. It will expire in 5 minutes."
    )
    return {"message": "OTP sent to email"}


@router.post("/verify-otp")
async def verify_otp(data: OTPVerifyRequest):
    redis = await get_redis()
    stored_otp = await redis.get(f"otp:{data.email}")

    if not stored_otp:
        raise HTTPException(status_code=400, detail="OTP expired or not found")
    if stored_otp != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # OTP is valid -> delete it from Redis
    await redis.delete(f"otp:{data.email}")
    return {"message": "Email verified successfully"}

#-------------Login Endpoint-------------
# Utility to check email across all tables
def get_user_and_role_by_email(email: str, db: Session):
    # Admins
    user = db.query(models.admin).filter(models.admin.email == email).first()
    if user:
        return user, "admin"

    # Recruiters
    user = db.query(models.recruiter).filter(models.recruiter.email == email).first()
    if user:
        return user, "recruiter"

    # Consultant Profiles
    user = db.query(models.ConsultantProfile).filter(models.ConsultantProfile.primary_email == email).first()
    if user:
        return user, "user"

    return None, None


@router.post("/login", response_model=schemas.LoginResponse)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user, role = get_user_and_role_by_email(data.email, db)

    if not user or not bcrypt.verify(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token_data = {"sub": data.email, "role": role}
    access_token = create_access_token(token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role,
        "user_id": user.id 
    }

#-------------User Profile Endpoints-------------
@router.get("/profile")
def get_user_profile(
    token: str = Depends(oauth2_scheme),
    x_user_id: int = Header(..., alias="X-User-Id"),
    x_user_role: str = Header(..., alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    # Validate the token
    try:
        payload = verify_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Fetch user from the appropriate table
    if x_user_role == "user":
        user = db.query(ConsultantProfile).filter(ConsultantProfile.id == x_user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"name": user.name, "email": user.primary_email}

    elif x_user_role == "recruiter":
        user = db.query(recruiter).filter(recruiter.id == x_user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Recruiter not found")
        return {"name": user.name, "email": user.email, "company": user.company_name}

    elif x_user_role == "admin":
        user = db.query(admin).filter(admin.id == x_user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Admin not found")
        return {"name": user.name, "email": user.email}

    else:
        raise HTTPException(status_code=400, detail="Invalid role")



# ---------- Resume  ----------
@router.post("/upload-resume")
async def upload_resume(
    consultant_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(status_code=400, detail="Only PDF or DOCX files are allowed.")

    file_data = await file.read()

    resume = Resume(
        consultant_id=consultant_id,
        file_name=file.filename,
        file_type=file.content_type,
        file_data=file_data
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return {"message": "Resume uploaded successfully", "resume_id": resume.id}

@router.get("/get-resume/{consultant_id}")
def get_resume(consultant_id: int, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.consultant_id == consultant_id).order_by(Resume.uploaded_at.desc()).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    return StreamingResponse(BytesIO(resume.file_data), media_type=resume.file_type, headers={
        "Content-Disposition": f"attachment; filename={resume.file_name}"
    })

#---------- new job description ----------
@router.post("/new-job", response_model=JobResponse)
def post_job(job: JobCreate, db: Session = Depends(get_db)):
    new_job = Job(**job.dict())
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job

#---------- Get all jobs ----------
@router.get("/jobs/", response_model=List[JobResponse])
def get_jobs(db: Session = Depends(get_db)):
    return db.query(Job).all()

@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

#---------- Apply for Job ----------
@router.post("/apply", response_model=JobApplicationResponse)
def apply_to_job(application: JobApplicationCreate, db: Session = Depends(get_db)):
    # Check if job exists
    job = db.query(Job).filter(Job.id == application.job_id).first()  # updated Job here
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check if consultant exists
    consultant = db.query(ConsultantProfile).filter(ConsultantProfile.id == application.consultant_id).first()
    if not consultant:
        raise HTTPException(status_code=404, detail="Consultant not found")

    # Check if consultant already applied for this job
    existing_application = (
        db.query(JobApplication)
        .filter(
            JobApplication.job_id == application.job_id,
            JobApplication.consultant_id == application.consultant_id
        )
        .first()
    )
    if existing_application:
        raise HTTPException(status_code=400, detail="You have already applied to this job")

    # Create new application
    new_application = JobApplication(job_id=application.job_id, consultant_id=application.consultant_id)
    db.add(new_application)
    db.commit()
    db.refresh(new_application)

    return new_application

#---------- Rank job applications ----------
@router.post("/rank-job-applicants", response_model=List[ApplicantRankedMatch])
def rank_job_applicants(request: RankApplicantsRequest, db: Session = Depends(get_db)):
    # Fetch the job
    job = db.query(Job).filter(Job.id == request.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Fetch all applicants for this job
    applications = db.query(JobApplication).filter(JobApplication.job_id == job.id).all()
    if not applications:
        raise HTTPException(status_code=404, detail="No applicants found for this job.")

    # Fetch recruiter
    recruiter_obj = db.query(recruiter).filter(recruiter.id == job.recruiter_id).first() if job.recruiter_id else None

    # Prepare job description
    job_input = JobDescription(
        title=job.job_title,
        company=recruiter_obj.company_name if recruiter_obj else "YourCompany",
        description=job.job_description or "",
        required_skills=job.required_skills if isinstance(job.required_skills, list) else [],
        preferred_skills=job.preferred_skills if isinstance(job.preferred_skills, list) else [],
        experience_level=getattr(job, "experience_level", "Any"),
        location=job.location or "Remote"
    )


    matcher = ResumeJDMatcher(model="gemma3:1b")
    results = []

    # Clear previous matches
    db.query(RankedApplicantMatch).filter(RankedApplicantMatch.job_id == job.id).delete()

    for application in applications:
        consultant = db.query(ConsultantProfile).filter(ConsultantProfile.id == application.consultant_id).first()
        resume = (
            db.query(Resume)
            .filter(Resume.consultant_id == application.consultant_id)
            .order_by(Resume.uploaded_at.desc())
            .first()
        )

        if not resume or not resume.file_data:
            continue

        # Save binary data to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(resume.file_data)
            tmp_file_path = tmp_file.name

        try:
            # Process resume and match
            result = matcher.match_resume_to_job(tmp_file_path, job_input)
            resume_data = matcher.process_resume(tmp_file_path)
            report = matcher.generate_report(result, resume_data, job_input)

            # Save to database
            db_match = RankedApplicantMatch(
                job_id=job.id,
                consultant_id=consultant.id,
                match_score=float(result.overall_score),
                top_skills_matched=",".join(result.matching_skills),  # Convert list to comma-separated string
                missing_skills=",".join(result.missing_skills),
                report=report,
                created_at=datetime.utcnow()
            )
            db.add(db_match)

            # Append to results
            results.append(ApplicantRankedMatch(
                consultant_id=consultant.id,
                consultant_name=consultant.name,
                match_score=result.overall_score,
                top_skills_matched=result.matching_skills,
                missing_skills=result.missing_skills,
                report=report
            ))

        except Exception as e:
            print(f"Error processing consultant {consultant.id}: {e}")
            continue
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    db.commit()
    results.sort(key=lambda x: x.match_score, reverse=True)
    return results

#---------- Test Email ----------
@router.post("/test-email")
def test_email():
    send_email_task.delay(
        to_email="poageshn@gmail.com",
        subject="Test Email from Celery",
        message="Hello! This is a test email sent from Celery via FastAPI."
    )
    return {"status": "email task dispatched"}