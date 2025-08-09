# app/schemas.py
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from fastapi import UploadFile, File

class RegisterInput(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str

#-------------CRUD Recruiter-------------
class RecruiterCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone_number: str
    company_name: str
    designation: str
    company_website: Optional[str]
    industry: str
    company_type: str
class RecruiterUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None  # If provided, hash before updating
    phone_number: Optional[str] = None
    company_name: Optional[str] = None
    designation: Optional[str] = None
    company_website: Optional[str] = None
    industry: Optional[str] = None
    company_type: Optional[str] = None

class RecruiterResponse(BaseModel):
    id: int
    name: str
    email: str
    phone_number: str
    company_name: str
    designation: str
    company_website: Optional[str]
    industry: str
    company_type: str
    # Exclude password for security in responses

    class Config:
        from_attributes = True

#------------CRUD admin -----------------
class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class AdminUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None  # If updating, hash if provided

class AdminResponse(BaseModel):
    id: int
    name: str
    email: str
    # Exclude password for security in responses

    class Config:
        from_attributes = True

# ---------- Nested Schemas for Related Tables ----------

class EducationDetailInput(BaseModel):
    level: str                       # "college", "class_x", "class_xii", "diploma", etc.
    institution_name: str
    degree: Optional[str] = None
    specialization: Optional[str] = None
    register_number: Optional[str] = None
    cgpa: Optional[float] = None
    board: Optional[str] = None
    year_of_pass_out: int
    percentage: Optional[float] = None

class ProjectInput(BaseModel):
    project_title: str
    techstack: str
    description: str
    project_link: Optional[str] = None

class TechnicalSkillInput(BaseModel):
    skill: str

class LanguageInput(BaseModel):
    language: str

class SubjectInput(BaseModel):
    subject: str

class ExperienceInput(BaseModel):
    job_role: str
    organization: str
    duration: str
    description: str

class AchievementInput(BaseModel):
    title: str
    description: str

class ExtraCurricularInput(BaseModel):
    title: str
    description: str

# ---------- Main Profile Schema ----------

class ProfileInput(BaseModel):
    # Basic Information
    name: str
    dob: Optional[date] = None
    gender: Optional[str] = None
    college: Optional[str] = None
    institution_roll_no: Optional[str] = None
    primary_email: EmailStr
    personal_email: Optional[EmailStr] = None
    mobile_no: Optional[str] = None
    password: str

    # Permanent Address
    country: Optional[str] = None
    pincode: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    address_line: Optional[str] = None

    # Related Tables (Nested Lists)
    education_details: List[EducationDetailInput]
    projects: List[ProjectInput]
    technical_skills: List[TechnicalSkillInput]
    languages: List[LanguageInput]
    subjects: List[SubjectInput]
    experiences: List[ExperienceInput]
    achievements: List[AchievementInput]
    extra_curricular_activities: List[ExtraCurricularInput]

    # Resume file path or URL
    # resume:  UploadFile = File(...)



# ---------- Response Schemas (with IDs) ----------

class EducationDetailResponse(EducationDetailInput):
    id: int
    class Config:
        from_attributes = True

class ProjectResponse(ProjectInput):
    id: int
    class Config:
        from_attributes = True

class TechnicalSkillResponse(TechnicalSkillInput):
    id: int
    class Config:
        from_attributes = True

class LanguageResponse(LanguageInput):
    id: int
    class Config:
        from_attributes = True

class SubjectResponse(SubjectInput):
    id: int
    class Config:
        from_attributes = True

class ExperienceResponse(ExperienceInput):
    id: int
    class Config:
        from_attributes = True

class AchievementResponse(AchievementInput):
    id: int
    class Config:
        from_attributes = True

class ExtraCurricularResponse(ExtraCurricularInput):
    id: int
    class Config:
        from_attributes = True

class ProfileResponse(BaseModel):
    id: int
    name: str
    primary_email: EmailStr
    dob: Optional[date]
    gender: Optional[str]
    college: Optional[str]
    institution_roll_no: Optional[str]
    personal_email: Optional[EmailStr]
    mobile_no: Optional[str]
    country: Optional[str]
    pincode: Optional[str]
    state: Optional[str]
    district: Optional[str]
    city: Optional[str]
    address_line: Optional[str]
    # resume: Optional[str]

    education_details: List[EducationDetailResponse]
    projects: List[ProjectResponse]
    technical_skills: List[TechnicalSkillResponse]
    languages: List[LanguageResponse]
    subjects: List[SubjectResponse]
    experiences: List[ExperienceResponse]
    achievements: List[AchievementResponse]
    extra_curricular_activities: List[ExtraCurricularResponse]

    class Config:
        from_attributes = True


#--------------OTP Verification Schemas-------------

class EmailRequest(BaseModel):
    email: EmailStr

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

#--------------login Schemas-------------  

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int

#-------------User Profile Endpoints-------------
class UserProfile(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


#--------------Job Description Schemas-------------
class JobCreate(BaseModel):
    recruiter_id: int
    job_title: str
    experience_level: str
    job_description: Optional[str]
    location: Optional[str]
    employment_type: Optional[str]
    required_skills: List[str]
    preferred_skills: Optional[List[str]]
    salary_range: Optional[str]
    deadline_to_apply: Optional[datetime]  

class JobResponse(JobCreate):
    id: int
    created_at: datetime  

    class Config:
        from_attributes = True

class JobUpdate(BaseModel):
    job_title: Optional[str]
    experience_level: Optional[str]
    job_description: Optional[str]
    location: Optional[str]
    employment_type: Optional[str]
    required_skills: Optional[List[str]]
    preferred_skills: Optional[List[str]]
    salary_range: Optional[str]
    deadline_to_apply: Optional[datetime]

#--------------Job Application Schemas-------------
class JobApplicationCreate(BaseModel):
    job_id: int
    consultant_id: int

class JobApplicationUpdate(BaseModel):
    job_id: int | None = None
    consultant_id: int | None = None

class JobApplicationResponse(BaseModel):
    id: int
    job_id: int
    consultant_id: int
    applied_at: datetime

    class Config:
        from_attributes = True

#-------------- Rank Job Application Schemas -------------

class RankApplicantsRequest(BaseModel):
    job_id: int

class ApplicantRankedMatch(BaseModel):
    consultant_id: int
    consultant_name: str
    match_score: float
    top_skills_matched: List[str]
    missing_skills: List[str]
    report: str

class RankedApplicantMatchInput(BaseModel):
    job_id: int
    consultant_id: int
    match_score: float
    top_skills_matched: List[str]
    missing_skills: List[str]
    report: str

#--------------- CRUD for Match Results -------------
class MatchResultCreate(BaseModel):
    jd_id: int
    profile_id: int
    similarity_score: float

class MatchResultUpdate(BaseModel):
    jd_id: int | None = None
    profile_id: int | None = None
    similarity_score: float | None = None

class MatchResultOut(BaseModel):
    id: int
    jd_id: int
    profile_id: int
    similarity_score: float

    class Config:
        from_attributes = True

#--------------------RankedApplicantMatch--------------------
class RankedApplicantMatchCreate(BaseModel):
    job_id: int
    consultant_id: int
    match_score: float
    top_skills_matched: Dict[str, Any] | None = None
    missing_skills: Dict[str, Any] | None = None
    report: str | None = None

class RankedApplicantMatchUpdate(BaseModel):
    job_id: int | None = None
    consultant_id: int | None = None
    match_score: float | None = None
    top_skills_matched: Dict[str, Any] | None = None
    missing_skills: Dict[str, Any] | None = None
    report: str | None = None

class RankedApplicantMatchResponse(BaseModel):
    id: int
    job_id: int
    consultant_id: int
    match_score: float
    top_skills_matched: Dict[str, Any] | None
    missing_skills: Dict[str, Any] | None
    report: str | None
    created_at: datetime

    class Config:
        from_attributes = True