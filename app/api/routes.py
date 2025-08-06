# app/api/routes.py
import random
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from starlette.responses import StreamingResponse
from io import BytesIO
import json
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, schemas, tasks
from app.models import ConsultantProfile, EducationDetail, Project, TechnicalSkill, Language, Subject, Experience, Achievement, ExtraCurricular, Resume
from app.schemas import ProfileInput, ProfileResponse, EmailRequest, OTPVerifyRequest
from app.tasks import send_email_task
from app.redis_manager import get_redis
from app.config import settings
from app.crud import create_recruiter
from passlib.context import CryptContext
from datetime import datetime
from app import auth
from passlib.hash import bcrypt




router = APIRouter()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

@router.post("/register-recruiter", response_model=schemas.RecruiterCreate)
def register_recruiter(recruiter: schemas.RecruiterCreate, db: Session = Depends(get_db)):
    return create_recruiter(db, recruiter)

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

# ---------- Get All Profiles ----------
@router.get("/profiles/", response_model=List[ProfileResponse])
def get_profiles(db: Session = Depends(get_db)):
    return db.query(ConsultantProfile).all()

# ---------- Get Single Profile ----------
@router.get("/profiles/{profile_id}", response_model=ProfileResponse)
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(ConsultantProfile).filter(ConsultantProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
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
    access_token = auth.create_access_token(token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role,
        "user_id": user.id 
    }


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