from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging

from app.core.config import settings
from app.api import auth, jobs, users, resumes, admin
from app.services.job_scheduler import scheduler_instance

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown"""
    # Startup
    logger.info("Starting Jobright AI API...")
    
    # Start job scraping scheduler if enabled
    try:
        if settings.SCRAPING_ENABLED:
            logger.info("Starting job scraping scheduler...")
            scheduler_instance.start()
        else:
            logger.info("Job scraping is disabled")
    except Exception as e:
        logger.warning(f"Failed to start scheduler: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Jobright AI API...")
    try:
        await scheduler_instance.shutdown()
    except Exception as e:
        logger.warning(f"Error during scheduler shutdown: {str(e)}")

app = FastAPI(
    title="Jobright AI API",
    description="AI-powered job search platform API with automated job scraping",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS + ["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/")
async def root():
    return {
        "message": "Jobright AI API",
        "version": "1.0.0",
        "features": [
            "Job Search & Matching",
            "Resume Analysis & Optimization", 
            "Automated Job Scraping",
            "User Management",
            "Application Tracking"
        ]
    }

@app.get("/health")
async def health_check():
    """Enhanced health check with system status"""
    try:
        status = {
            "status": "healthy",
            "api_version": "1.0.0",
            "scraping_enabled": settings.SCRAPING_ENABLED,
            "scheduler_running": False,  # Simplified for now
            "environment": getattr(settings, 'ENVIRONMENT', 'production')
        }
        return status
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}