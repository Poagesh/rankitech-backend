# app/schemas.py
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date

class RegisterInput(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str

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

class JDInput(BaseModel):
    title: str
    content: str

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
    resume: Optional[str] = None



# ---------- Response Schemas (with IDs) ----------

class EducationDetailResponse(EducationDetailInput):
    id: int
    class Config:
        orm_mode = True

class ProjectResponse(ProjectInput):
    id: int
    class Config:
        orm_mode = True

class TechnicalSkillResponse(TechnicalSkillInput):
    id: int
    class Config:
        orm_mode = True

class LanguageResponse(LanguageInput):
    id: int
    class Config:
        orm_mode = True

class SubjectResponse(SubjectInput):
    id: int
    class Config:
        orm_mode = True

class ExperienceResponse(ExperienceInput):
    id: int
    class Config:
        orm_mode = True

class AchievementResponse(AchievementInput):
    id: int
    class Config:
        orm_mode = True

class ExtraCurricularResponse(ExtraCurricularInput):
    id: int
    class Config:
        orm_mode = True

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
    resume: Optional[str]

    education_details: List[EducationDetailResponse]
    projects: List[ProjectResponse]
    technical_skills: List[TechnicalSkillResponse]
    languages: List[LanguageResponse]
    subjects: List[SubjectResponse]
    experiences: List[ExperienceResponse]
    achievements: List[AchievementResponse]
    extra_curricular_activities: List[ExtraCurricularResponse]

    class Config:
        orm_mode = True


#--------------OTP Verification Schemas-------------

class EmailRequest(BaseModel):
    email: EmailStr

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str


