from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.services.resume_service import ResumeService
from pydantic import BaseModel
from typing import Optional, List
import os

router = APIRouter()

class ResumeAnalysis(BaseModel):
    score: float
    strengths: List[str]
    improvements: List[str]
    ats_score: float
    extracted_skills: List[str]
    experience_years: Optional[int]

class ResumeOptimization(BaseModel):
    optimized_content: str
    suggestions: List[str]
    keyword_improvements: List[str]

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")
    
    upload_dir = "uploads/resumes"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = f"{upload_dir}/{current_user.id}_{file.filename}"
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    current_user.resume_url = file_path
    db.commit()
    
    return {"message": "Resume uploaded successfully", "file_path": file_path}

@router.get("/analyze", response_model=ResumeAnalysis)
async def analyze_resume(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.resume_url:
        raise HTTPException(status_code=400, detail="No resume uploaded")
    
    resume_service = ResumeService()
    analysis = resume_service.analyze_resume(current_user.resume_url)
    
    current_user.skills = analysis["extracted_skills"]
    db.commit()
    
    return ResumeAnalysis(**analysis)

@router.post("/optimize")
async def optimize_resume(
    job_description: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.resume_url:
        raise HTTPException(status_code=400, detail="No resume uploaded")
    
    resume_service = ResumeService()
    optimization = resume_service.optimize_for_job(current_user.resume_url, job_description)
    
    return ResumeOptimization(**optimization)