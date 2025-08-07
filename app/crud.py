from sqlalchemy.orm import Session
from . import models, schemas
from app.models import ConsultantProfile, EducationDetail, Project, TechnicalSkill, Language, Subject, Experience, Achievement, ExtraCurricular
from app.schemas import ProfileInput
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_recruiter(db: Session, recruiter: schemas.RecruiterCreate):
    hashed_password = hash_password(recruiter.password)

    db_recruiter = models.recruiter(
        name=recruiter.name,
        email=recruiter.email,
        password=hashed_password,
        phone_number=recruiter.phone_number,
        designation=recruiter.designation,
        company_name=recruiter.company_name,
        company_website=recruiter.company_website,
        industry=recruiter.industry,
        company_type=recruiter.company_type
    )

    db.add(db_recruiter)
    db.commit()
    db.refresh(db_recruiter)
    return db_recruiter


def create_consultant_profile(db: Session, profile_in: ProfileInput):
    profile = ConsultantProfile(
        name=profile_in.name,
        dob=profile_in.dob,
        gender=profile_in.gender,
        college=profile_in.college,
        institution_roll_no=profile_in.institution_roll_no,
        primary_email=profile_in.primary_email,
        personal_email=profile_in.personal_email,
        mobile_no=profile_in.mobile_no,
        password=profile_in.password,  # Ideally hash password before saving!
        country=profile_in.country,
        pincode=profile_in.pincode,
        state=profile_in.state,
        district=profile_in.district,
        city=profile_in.city,
        address_line=profile_in.address_line,
        resume=profile_in.resume
    )

    # Add related entities
    profile.education_details = [
        EducationDetail(**ed.dict()) for ed in profile_in.education_details
    ]
    profile.projects = [
        Project(**proj.dict()) for proj in profile_in.projects
    ]
    profile.technical_skills = [
        TechnicalSkill(**skill.dict()) for skill in profile_in.technical_skills
    ]
    profile.languages = [
        Language(**lang.dict()) for lang in profile_in.languages
    ]
    profile.subjects = [
        Subject(**sub.dict()) for sub in profile_in.subjects
    ]
    profile.experiences = [
        Experience(**exp.dict()) for exp in profile_in.experiences
    ]
    profile.achievements = [
        Achievement(**ach.dict()) for ach in profile_in.achievements
    ]
    profile.extra_curricular_activities = [
        ExtraCurricular(**act.dict()) for act in profile_in.extra_curricular_activities
    ]

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
