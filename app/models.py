# app/models.py
from sqlalchemy import Column, Integer, String, Text, Float, Date, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# ---------- Admin Table ----------
class admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # In production, hash the password


#-- Recruiter Table ----------
class recruiter(Base):
    __tablename__ = "recruiters"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # In production, hash the password
    phone_number = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    designation = Column(String, nullable=False)
    company_website = Column(String, nullable=True)
    industry = Column(String, nullable=False)
    company_type = Column(String, nullable=False)    

# ---------- Job Description Table ----------
class JobDescription(Base):
    __tablename__ = "job_descriptions"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(Text)
    skills_required = Column(String)
    start_date = Column(String)
    end_date = Column(String)


# ---------- Match Result Table ----------
class MatchResult(Base):
    __tablename__ = "match_results"
    id = Column(Integer, primary_key=True)
    jd_id = Column(Integer)
    profile_id = Column(Integer)
    similarity_score = Column(Float)

# ---------- Main Profile Table ----------
class ConsultantProfile(Base):
    __tablename__ = "consultant_profiles"
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Basic Information
    name = Column(String, nullable=False)
    dob = Column(Date)
    gender = Column(String)
    college = Column(String)
    institution_roll_no = Column(String)
    primary_email = Column(String, unique=True, nullable=False)
    personal_email = Column(String)
    mobile_no = Column(String)
    password = Column(String)

    # Permanent Address
    country = Column(String)
    pincode = Column(String)
    state = Column(String)
    district = Column(String)
    city = Column(String)
    address_line = Column(Text)

    # Resume (file path or URL)
    resume = Column(String)

    # Relationships
    education_details = relationship("EducationDetail", back_populates="profile", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="profile", cascade="all, delete-orphan")
    technical_skills = relationship("TechnicalSkill", back_populates="profile", cascade="all, delete-orphan")
    languages = relationship("Language", back_populates="profile", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="profile", cascade="all, delete-orphan")
    experiences = relationship("Experience", back_populates="profile", cascade="all, delete-orphan")
    achievements = relationship("Achievement", back_populates="profile", cascade="all, delete-orphan")
    extra_curricular_activities = relationship("ExtraCurricular", back_populates="profile", cascade="all, delete-orphan")


# ---------- Education ----------
class EducationDetail(Base):
    __tablename__ = "education_details"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("consultant_profiles.id"))

    level = Column(String)  # college, class_x, class_xii, diploma etc.
    institution_name = Column(String)
    degree = Column(String, nullable=True)  # For college level
    specialization = Column(String, nullable=True)
    register_number = Column(String, nullable=True)
    cgpa = Column(Float, nullable=True)
    board = Column(String, nullable=True)
    year_of_pass_out = Column(Integer)
    percentage = Column(Float, nullable=True)

    profile = relationship("ConsultantProfile", back_populates="education_details")


# ---------- Projects ----------
class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("consultant_profiles.id"))

    project_title = Column(String)
    techstack = Column(String)
    description = Column(Text)
    project_link = Column(String, nullable=True)

    profile = relationship("ConsultantProfile", back_populates="projects")


# ---------- Skills ----------
class TechnicalSkill(Base):
    __tablename__ = "technical_skills"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("consultant_profiles.id"))

    skill = Column(String)
    profile = relationship("ConsultantProfile", back_populates="technical_skills")

class Language(Base):
    __tablename__ = "languages"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("consultant_profiles.id"))

    language = Column(String)
    profile = relationship("ConsultantProfile", back_populates="languages")

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("consultant_profiles.id"))

    subject = Column(String)
    profile = relationship("ConsultantProfile", back_populates="subjects")


# ---------- Experiences ----------
class Experience(Base):
    __tablename__ = "experiences"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("consultant_profiles.id"))

    job_role = Column(String)
    organization = Column(String)
    duration = Column(String)
    description = Column(Text)

    profile = relationship("ConsultantProfile", back_populates="experiences")


# ---------- Achievements ----------
class Achievement(Base):
    __tablename__ = "achievements"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("consultant_profiles.id"))

    title = Column(String)
    description = Column(Text)

    profile = relationship("ConsultantProfile", back_populates="achievements")


# ---------- Extra Curricular ----------
class ExtraCurricular(Base):
    __tablename__ = "extra_curricular"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("consultant_profiles.id"))

    title = Column(String)
    description = Column(Text)

    profile = relationship("ConsultantProfile", back_populates="extra_curricular_activities")

