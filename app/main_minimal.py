from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="Jobright AI API",
    description="AI-powered job search platform API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Jobright AI API",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "Job Search & Matching",
            "Resume Analysis & Optimization", 
            "User Management",
            "Application Tracking"
        ]
    }

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "production")
    }

@app.get("/api/test")
async def test_endpoint():
    """Test API endpoint"""
    return {
        "message": "API is working correctly",
        "timestamp": "2024-09-06",
        "endpoint": "/api/test"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)