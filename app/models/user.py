from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    phone = Column(String)
    location = Column(String)
    job_title = Column(String)
    experience_level = Column(String)
    experience_years = Column(Integer)
    salary_expectation = Column(Integer)
    preferred_job_types = Column(JSON)
    preferred_remote_types = Column(JSON)
    skills = Column(JSON)
    job_preferences = Column(JSON)
    resume_url = Column(String)
    profile_summary = Column(Text)
    
    applications = relationship("JobApplication", back_populates="user")
    saved_jobs = relationship("SavedJob", back_populates="user")