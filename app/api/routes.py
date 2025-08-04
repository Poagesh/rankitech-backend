# app/api/routes.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, schemas, tasks
from app.models import ConsultantProfile, EducationDetail, Project, TechnicalSkill, Language, Subject, Experience, Achievement, ExtraCurricular
from app.schemas import ProfileInput, ProfileResponse, EmailRequest, OTPVerifyRequest
from app.tasks import send_email_task
from app.redis_manager import get_redis
import random
from app.config import settings

router = APIRouter()

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

# ---------- Create Profile ----------
@router.post("/profiles/", response_model=ProfileResponse)
def create_profile(profile_data: ProfileInput, db: Session = Depends(get_db)):
    # Check if email already exists
    existing = db.query(ConsultantProfile).filter(ConsultantProfile.primary_email == profile_data.primary_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create main profile
    profile = ConsultantProfile(
        name=profile_data.name,
        dob=profile_data.dob,
        gender=profile_data.gender,
        college=profile_data.college,
        institution_roll_no=profile_data.institution_roll_no,
        primary_email=profile_data.primary_email,
        personal_email=profile_data.personal_email,
        mobile_no=profile_data.mobile_no,
        password=profile_data.password,  # In production, hash the password
        country=profile_data.country,
        pincode=profile_data.pincode,
        state=profile_data.state,
        district=profile_data.district,
        city=profile_data.city,
        address_line=profile_data.address_line,
        resume=profile_data.resume
    )

    # Add related records
    profile.education_details = [EducationDetail(**ed.dict()) for ed in profile_data.education_details]
    profile.projects = [Project(**p.dict()) for p in profile_data.projects]
    profile.technical_skills = [TechnicalSkill(**s.dict()) for s in profile_data.technical_skills]
    profile.languages = [Language(**l.dict()) for l in profile_data.languages]
    profile.subjects = [Subject(**sub.dict()) for sub in profile_data.subjects]
    profile.experiences = [Experience(**e.dict()) for e in profile_data.experiences]
    profile.achievements = [Achievement(**a.dict()) for a in profile_data.achievements]
    profile.extra_curricular_activities = [ExtraCurricular(**ec.dict()) for ec in profile_data.extra_curricular_activities]

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