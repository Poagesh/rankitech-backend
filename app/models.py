from sqlalchemy import Column, Integer, String, Text, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class JobDescription(Base):
    __tablename__ = "job_descriptions"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(Text)

class ConsultantProfile(Base):
    __tablename__ = "consultant_profiles"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    content = Column(Text)

class MatchResult(Base):
    __tablename__ = "match_results"
    id = Column(Integer, primary_key=True)
    jd_id = Column(Integer)
    profile_id = Column(Integer)
    similarity_score = Column(Float)
