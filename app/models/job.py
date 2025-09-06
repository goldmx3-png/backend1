from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    company_name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    requirements = Column(Text)
    location = Column(String, index=True)
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    salary_currency = Column(String, default="USD")
    job_type = Column(String, index=True)  # full-time, part-time, contract
    remote_type = Column(String, index=True)  # remote, hybrid, on-site
    experience_level = Column(String, index=True)
    skills_required = Column(JSON)
    benefits = Column(JSON)
    posted_date = Column(DateTime(timezone=True))
    application_deadline = Column(DateTime(timezone=True))
    external_url = Column(String)
    source = Column(String)  # indeed, remoteok, etc.
    application_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    company_id = Column(Integer, ForeignKey("companies.id"))
    company = relationship("Company", back_populates="jobs")
    applications = relationship("JobApplication", back_populates="job")
    saved_by_users = relationship("SavedJob", back_populates="job")

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text)
    website = Column(String)
    logo_url = Column(String)
    size = Column(String)
    industry = Column(String)
    location = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    jobs = relationship("Job", back_populates="company")

class JobApplication(Base):
    __tablename__ = "job_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    status = Column(String, default="applied")  # applied, interviewing, rejected, offered
    applied_date = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)
    resume_version = Column(String)
    cover_letter = Column(Text)
    
    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")

class SavedJob(Base):
    __tablename__ = "saved_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    saved_date = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)
    
    user = relationship("User", back_populates="saved_jobs")
    job = relationship("Job", back_populates="saved_by_users")