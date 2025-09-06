"""
Admin API endpoints for job scraping management
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.job import Job
from app.services.job_scheduler import scheduler_instance, get_scheduler_status
from app.services.enhanced_job_scraper import run_enhanced_job_scraper
from app.core.config import settings
from pydantic import BaseModel
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class ScrapingConfigUpdate(BaseModel):
    scraping_enabled: bool = None
    interval_minutes: int = None
    max_jobs_per_run: int = None

class ManualScrapeRequest(BaseModel):
    num_jobs: int = 100
    sources: List[str] = None

def is_admin(current_user: User = Depends(get_current_user)) -> User:
    """Check if current user is admin"""
    # In a real app, you'd have a proper admin role system
    if not current_user.email.endswith("@jobright.ai"):  # Simple admin check
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@router.get("/scraping/status")
async def get_scraping_status(admin: User = Depends(is_admin)):
    """Get current scraping scheduler status"""
    try:
        status = await get_scheduler_status()
        return status
    except Exception as e:
        logger.error(f"Error getting scraping status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scraping/stats")
async def get_scraping_stats(
    admin: User = Depends(is_admin),
    db: Session = Depends(get_db)
):
    """Get job scraping statistics"""
    try:
        # Get job count by source
        jobs_by_source = {}
        sources = db.query(Job.source).distinct().all()
        
        for (source,) in sources:
            count = db.query(Job).filter(Job.source == source).count()
            jobs_by_source[source] = count
        
        # Get recent jobs count
        from datetime import datetime, timedelta
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_jobs = db.query(Job).filter(Job.created_at >= recent_cutoff).count()
        
        total_jobs = db.query(Job).count()
        active_jobs = db.query(Job).filter(Job.is_active == True).count()
        
        return {
            "total_jobs": total_jobs,
            "active_jobs": active_jobs,
            "recent_jobs_7_days": recent_jobs,
            "jobs_by_source": jobs_by_source,
            "scraping_enabled": settings.SCRAPING_ENABLED,
            "last_update": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting scraping stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scraping/manual")
async def trigger_manual_scraping(
    request: ManualScrapeRequest,
    background_tasks: BackgroundTasks,
    admin: User = Depends(is_admin)
):
    """Manually trigger job scraping"""
    try:
        if not settings.SCRAPING_ENABLED:
            raise HTTPException(
                status_code=400, 
                detail="Scraping is disabled in configuration"
            )
        
        # Add scraping task to background
        background_tasks.add_task(run_enhanced_job_scraper, request.num_jobs)
        
        return {
            "message": f"Manual scraping started for {request.num_jobs} jobs",
            "status": "started"
        }
        
    except Exception as e:
        logger.error(f"Error triggering manual scraping: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/scraping/config")
async def update_scraping_config(
    config: ScrapingConfigUpdate,
    admin: User = Depends(is_admin)
):
    """Update scraping configuration (Note: requires restart to take effect)"""
    try:
        updates = {}
        
        # Note: In a production system, you'd want to persist these changes
        # to environment variables or a config file
        
        if config.scraping_enabled is not None:
            updates["scraping_enabled"] = config.scraping_enabled
            
        if config.interval_minutes is not None:
            if config.interval_minutes < 5:
                raise HTTPException(
                    status_code=400,
                    detail="Interval must be at least 5 minutes"
                )
            updates["interval_minutes"] = config.interval_minutes
            
        if config.max_jobs_per_run is not None:
            if config.max_jobs_per_run < 10 or config.max_jobs_per_run > 1000:
                raise HTTPException(
                    status_code=400,
                    detail="Max jobs per run must be between 10 and 1000"
                )
            updates["max_jobs_per_run"] = config.max_jobs_per_run
        
        return {
            "message": "Configuration updated (restart required to take effect)",
            "updates": updates,
            "current_config": {
                "scraping_enabled": settings.SCRAPING_ENABLED,
                "interval_minutes": settings.SCRAPING_INTERVAL_MINUTES,
                "max_jobs_per_run": settings.SCRAPING_MAX_JOBS_PER_RUN
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating scraping config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scraping/cleanup")
async def cleanup_old_jobs(
    days_old: int = 60,
    admin: User = Depends(is_admin),
    db: Session = Depends(get_db)
):
    """Clean up jobs older than specified days"""
    try:
        if days_old < 30:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete jobs newer than 30 days"
            )
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Count jobs to be deleted
        jobs_to_delete = db.query(Job).filter(Job.posted_date < cutoff_date).count()
        
        # Delete old jobs
        deleted_count = db.query(Job).filter(
            Job.posted_date < cutoff_date
        ).delete(synchronize_session=False)
        
        db.commit()
        
        return {
            "message": f"Cleanup completed",
            "deleted_jobs": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/health")
async def get_jobs_health(db: Session = Depends(get_db)):
    """Public health check endpoint for jobs system"""
    try:
        # Check database connectivity
        total_jobs = db.query(Job).count()
        
        # Check recent activity
        from datetime import datetime, timedelta
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_jobs = db.query(Job).filter(Job.created_at >= recent_cutoff).count()
        
        return {
            "status": "healthy",
            "total_jobs": total_jobs,
            "recent_jobs_24h": recent_jobs,
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }