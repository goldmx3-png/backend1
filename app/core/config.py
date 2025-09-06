from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Jobright AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://jobright:password@localhost/jobright_db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:8000"]
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Job Scraping Configuration
    SCRAPING_ENABLED: bool = os.getenv("SCRAPING_ENABLED", "true").lower() == "true"
    SCRAPING_INTERVAL_MINUTES: int = int(os.getenv("SCRAPING_INTERVAL_MINUTES", "60"))
    SCRAPING_MAX_JOBS_PER_RUN: int = int(os.getenv("SCRAPING_MAX_JOBS_PER_RUN", "200"))
    SCRAPING_CONCURRENT_REQUESTS: int = int(os.getenv("SCRAPING_CONCURRENT_REQUESTS", "5"))
    SCRAPING_DELAY_BETWEEN_REQUESTS: float = float(os.getenv("SCRAPING_DELAY_BETWEEN_REQUESTS", "2.0"))
    
    # Rate Limiting Configuration
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "100"))
    RATE_LIMIT_BURST_SIZE: int = int(os.getenv("RATE_LIMIT_BURST_SIZE", "20"))
    
    # Job Sources Configuration
    ENABLE_REMOTEOK: bool = os.getenv("ENABLE_REMOTEOK", "true").lower() == "true"
    ENABLE_YCOMBINATOR: bool = os.getenv("ENABLE_YCOMBINATOR", "true").lower() == "true"
    ENABLE_GITHUB_JOBS: bool = os.getenv("ENABLE_GITHUB_JOBS", "false").lower() == "true"
    ENABLE_STACKOVERFLOW_JOBS: bool = os.getenv("ENABLE_STACKOVERFLOW_JOBS", "false").lower() == "true"
    ENABLE_WELLFOUND: bool = os.getenv("ENABLE_WELLFOUND", "true").lower() == "true"
    ENABLE_OTTA: bool = os.getenv("ENABLE_OTTA", "true").lower() == "true"
    
    # External API Keys
    REMOTEOK_API_KEY: Optional[str] = os.getenv("REMOTEOK_API_KEY")
    WELLFOUND_API_KEY: Optional[str] = os.getenv("WELLFOUND_API_KEY")
    OTTA_API_KEY: Optional[str] = os.getenv("OTTA_API_KEY")
    
    # Proxy Configuration
    USE_PROXY_ROTATION: bool = os.getenv("USE_PROXY_ROTATION", "false").lower() == "true"
    PROXY_LIST: Optional[str] = os.getenv("PROXY_LIST")
    
    # User Agent Rotation
    USE_USER_AGENT_ROTATION: bool = os.getenv("USE_USER_AGENT_ROTATION", "true").lower() == "true"
    
    # Error Handling & Monitoring
    ENABLE_ERROR_NOTIFICATIONS: bool = os.getenv("ENABLE_ERROR_NOTIFICATIONS", "true").lower() == "true"
    ERROR_NOTIFICATION_EMAIL: Optional[str] = os.getenv("ERROR_NOTIFICATION_EMAIL")
    SLACK_WEBHOOK_URL: Optional[str] = os.getenv("SLACK_WEBHOOK_URL")
    
    # Performance Monitoring
    ENABLE_PERFORMANCE_MONITORING: bool = os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true"
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # Legacy settings for backward compatibility
    SCRAPING_RATE_LIMIT: int = int(os.getenv("SCRAPING_DELAY_BETWEEN_REQUESTS", "2"))
    MAX_CONCURRENT_REQUESTS: int = int(os.getenv("SCRAPING_CONCURRENT_REQUESTS", "5"))

    class Config:
        case_sensitive = True

settings = Settings()