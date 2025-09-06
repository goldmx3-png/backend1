from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.job import Job, Company, SavedJob, JobApplication
from app.services.job_matching import get_job_recommendations, calculate_match_score
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()

class CompanyInfo(BaseModel):
    id: Optional[int]
    name: str
    industry: Optional[str]
    size: Optional[str]
    location: Optional[str]

class JobResponse(BaseModel):
    id: int
    title: str
    company_name: str
    company: Optional[CompanyInfo]
    description: str
    location: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    job_type: Optional[str]
    remote_type: Optional[str]
    experience_level: Optional[str]
    skills_required: Optional[List[str]]
    posted_date: Optional[datetime]
    external_url: Optional[str]
    source: Optional[str]
    application_count: Optional[int] = 0
    view_count: Optional[int] = 0

class SaveJobRequest(BaseModel):
    notes: Optional[str] = None

class ApplyJobRequest(BaseModel):
    cover_letter: Optional[str] = None
    notes: Optional[str] = None

@router.get("/", response_model=List[JobResponse])
async def search_jobs(
    skip: int = 0,
    limit: int = 20,
    title: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    remote_type: Optional[str] = Query(None),
    experience_level: Optional[str] = Query(None),
    min_salary: Optional[int] = Query(None),
    max_salary: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Job).outerjoin(Company).filter(Job.is_active == True)
    
    if title:
        query = query.filter(or_(
            Job.title.ilike(f"%{title}%"),
            Job.description.ilike(f"%{title}%")
        ))
    
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    
    if job_type:
        query = query.filter(Job.job_type == job_type)
    
    if remote_type:
        query = query.filter(Job.remote_type == remote_type)
    
    if experience_level:
        query = query.filter(Job.experience_level == experience_level)
    
    if min_salary:
        query = query.filter(Job.salary_min >= min_salary)
    
    if max_salary:
        query = query.filter(Job.salary_max <= max_salary)
    
    jobs = query.offset(skip).limit(limit).all()
    
    # Transform jobs to include company info
    result = []
    for job in jobs:
        job_dict = {
            "id": job.id,
            "title": job.title,
            "company_name": job.company_name,
            "company": {
                "id": job.company.id if job.company else None,
                "name": job.company.name if job.company else job.company_name,
                "industry": job.company.industry if job.company else None,
                "size": job.company.size if job.company else None,
                "location": job.company.location if job.company else None,
            } if job.company else None,
            "description": job.description,
            "location": job.location,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "job_type": job.job_type,
            "remote_type": job.remote_type,
            "experience_level": job.experience_level,
            "skills_required": job.skills_required,
            "posted_date": job.posted_date,
            "external_url": job.external_url,
            "source": job.source,
            "application_count": job.application_count or 0,
            "view_count": job.view_count or 0,
        }
        result.append(job_dict)
    
    return result

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id, Job.is_active == True).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/{job_id}/save")
async def save_job(
    job_id: int,
    request: SaveJobRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    existing_save = db.query(SavedJob).filter(
        SavedJob.user_id == current_user.id,
        SavedJob.job_id == job_id
    ).first()
    
    if existing_save:
        raise HTTPException(status_code=400, detail="Job already saved")
    
    saved_job = SavedJob(
        user_id=current_user.id,
        job_id=job_id,
        notes=request.notes
    )
    db.add(saved_job)
    db.commit()
    
    return {"message": "Job saved successfully"}

@router.post("/{job_id}/apply")
async def apply_to_job(
    job_id: int,
    request: ApplyJobRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    existing_application = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id,
        JobApplication.job_id == job_id
    ).first()
    
    if existing_application:
        raise HTTPException(status_code=400, detail="Already applied to this job")
    
    application = JobApplication(
        user_id=current_user.id,
        job_id=job_id,
        cover_letter=request.cover_letter,
        notes=request.notes
    )
    db.add(application)
    db.commit()
    
    return {"message": "Application submitted successfully"}

@router.get("/saved/", response_model=List[JobResponse])
async def get_saved_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    saved_jobs_query = db.query(Job).join(SavedJob).filter(
        SavedJob.user_id == current_user.id
    ).all()
    
    # Transform to include company info like other endpoints
    result = []
    for job in saved_jobs_query:
        job_dict = {
            "id": job.id,
            "title": job.title,
            "company_name": job.company_name,
            "company": {
                "id": job.company.id if job.company else None,
                "name": job.company.name if job.company else job.company_name,
                "industry": job.company.industry if job.company else None,
                "size": job.company.size if job.company else None,
                "location": job.company.location if job.company else None,
            } if job.company else None,
            "description": job.description,
            "location": job.location,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "job_type": job.job_type,
            "remote_type": job.remote_type,
            "experience_level": job.experience_level,
            "skills_required": job.skills_required,
            "posted_date": job.posted_date,
            "external_url": job.external_url,
            "source": job.source,
            "application_count": job.application_count or 0,
            "view_count": job.view_count or 0,
        }
        result.append(job_dict)
    
    return result

@router.get("/applied/", response_model=List[JobResponse])
async def get_applied_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    applied_jobs_query = db.query(Job).join(JobApplication).filter(
        JobApplication.user_id == current_user.id
    ).all()
    
    # Transform to include company info
    result = []
    for job in applied_jobs_query:
        job_dict = {
            "id": job.id,
            "title": job.title,
            "company_name": job.company_name,
            "company": {
                "id": job.company.id if job.company else None,
                "name": job.company.name if job.company else job.company_name,
                "industry": job.company.industry if job.company else None,
                "size": job.company.size if job.company else None,
                "location": job.company.location if job.company else None,
            } if job.company else None,
            "description": job.description,
            "location": job.location,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "job_type": job.job_type,
            "remote_type": job.remote_type,
            "experience_level": job.experience_level,
            "skills_required": job.skills_required,
            "posted_date": job.posted_date,
            "external_url": job.external_url,
            "source": job.source,
            "application_count": job.application_count or 0,
            "view_count": job.view_count or 0,
        }
        result.append(job_dict)
    
    return result

@router.get("/recommendations/")
async def get_job_recommendations_endpoint(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized job recommendations based on user profile"""
    recommendations = get_job_recommendations(current_user.id, limit)
    
    # Get user stats for tabs
    saved_count = db.query(SavedJob).filter(SavedJob.user_id == current_user.id).count()
    applied_count = db.query(JobApplication).filter(JobApplication.user_id == current_user.id).count()
    
    return {
        "recommendations": recommendations,
        "total": len(recommendations),
        "user_id": current_user.id,
        "user_stats": {
            "liked_count": saved_count,
            "applied_count": applied_count,
            "external_count": 0  # External applications not tracked yet
        }
    }

@router.get("/user-preferences/")
async def get_user_job_preferences(
    current_user: User = Depends(get_current_user)
):
    """Get user's job preferences for filter tags"""
    user_skills = current_user.skills or []
    user_preferences = current_user.job_preferences or {}
    
    # Extract skills and preferences to show as active filters
    skill_filters = user_skills[:5] if user_skills else ['Python', 'JavaScript', 'React']
    location_filters = [current_user.location] if current_user.location else ['Remote', 'United States']
    job_type_filters = user_preferences.get('job_types', ['Full-time'])
    remote_type_filters = user_preferences.get('remote_type', ['Remote'])
    experience_filters = [current_user.experience_level] if current_user.experience_level else ['Mid Level']
    
    return {
        "skills": skill_filters,
        "locations": location_filters, 
        "job_types": job_type_filters,
        "remote_types": remote_type_filters,
        "experience_levels": experience_filters,
        "other_filters": ['H1B Only'] if user_preferences.get('needs_sponsorship') else []
    }

@router.get("/{job_id}/match-score/")
async def get_match_score(
    job_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get match score between current user and specific job"""
    match_data = calculate_match_score(current_user.id, job_id)
    
    if 'error' in match_data:
        raise HTTPException(status_code=404, detail=match_data['error'])
    
    return match_data