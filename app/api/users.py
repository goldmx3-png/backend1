from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    job_title: Optional[str] = None
    experience_level: Optional[str] = None
    skills: Optional[List[str]] = None
    job_preferences: Optional[dict] = None
    profile_summary: Optional[str] = None

class UserProfile(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    location: Optional[str]
    job_title: Optional[str]
    experience_level: Optional[str]
    skills: Optional[List[str]]
    job_preferences: Optional[dict]
    profile_summary: Optional[str]
    resume_url: Optional[str]

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserProfile)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user