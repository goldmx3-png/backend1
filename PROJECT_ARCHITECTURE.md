# JobRight AI Backend Architecture

## 🏗️ Project Structure Overview

The JobRight AI backend is a FastAPI-based application with a layered architecture designed for scalability, maintainability, and AI-powered job matching.

### 📁 Directory Structure

```
backend/
├── app/                          # Main application package
│   ├── api/                     # API route handlers (Controllers)
│   │   ├── auth.py              # Authentication & user management
│   │   ├── jobs.py              # Job search, filtering, applications
│   │   ├── users.py             # User profiles & preferences
│   │   ├── resumes.py           # Resume processing & optimization
│   │   └── admin.py             # Administrative functions
│   ├── core/                    # Core configuration & utilities
│   │   ├── config.py            # Environment settings & configuration
│   │   ├── database.py          # Database connection management
│   │   └── security.py          # JWT tokens & authentication utilities
│   ├── models/                  # Database models (SQLAlchemy)
│   │   ├── user.py              # User, profile, preferences models
│   │   └── job.py               # Job, Company, Application models
│   ├── services/                # Business logic services
│   │   ├── enhanced_job_scraper.py  # Multi-source web scraping
│   │   ├── job_matching.py      # AI job-user matching algorithm
│   │   ├── job_scheduler.py     # Background job automation
│   │   └── resume_service.py    # Resume analysis & optimization
│   ├── utils/                   # Utility functions
│   └── main.py                  # FastAPI application entry point
├── alembic/                     # Database migrations
│   ├── versions/                # Migration history
│   └── env.py                   # Alembic configuration
├── render.yaml                  # Render deployment configuration
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── SECURITY.md                  # Security configuration guide
└── PROJECT_ARCHITECTURE.md     # This documentation
```

## 🔧 Component Architecture

### 1. **Application Layer** (`main.py`)
- **FastAPI Application**: Main application factory with middleware
- **CORS Middleware**: Cross-origin request handling for frontend
- **Lifespan Management**: Startup/shutdown handlers for background services
- **Health Check**: System status monitoring endpoint
- **Router Integration**: API endpoint organization

### 2. **API Layer** (`app/api/`)
Route handlers following RESTful principles:

- **Authentication (`auth.py`)**:
  - User registration and login
  - JWT token generation and validation
  - Password reset functionality

- **Jobs (`jobs.py`)**:
  - Job search with filtering and pagination
  - Job recommendations based on user profile
  - Save/unsave jobs functionality
  - Job application tracking

- **Users (`users.py`)**:
  - User profile management
  - Job preferences and settings
  - Application history

- **Resumes (`resumes.py`)**:
  - Resume upload and parsing
  - AI-powered resume optimization
  - Template generation

- **Admin (`admin.py`)**:
  - System administration
  - User management
  - Analytics and reporting

### 3. **Data Layer** (`app/models/`)
SQLAlchemy ORM models with relationships:

- **User Model**: Authentication + extended profile data
- **Job Model**: Complete job listings with metadata
- **Company Model**: Employer information and relationships  
- **JobApplication Model**: User application tracking
- **SavedJob Model**: User job bookmarks

### 4. **Business Logic Layer** (`app/services/`)
Core business services:

- **Job Scraper**: Multi-source data collection from job boards
- **Matching Algorithm**: AI-powered job-user compatibility scoring
- **Scheduler**: Automated background job processing
- **Resume Service**: Document processing and analysis

### 5. **Core Infrastructure** (`app/core/`)
Foundational components:

- **Configuration**: Environment-based settings management
- **Database**: Connection pooling and session management
- **Security**: JWT authentication and password hashing

## 🔄 Data Flow Architecture

### User Request Flow
```mermaid
Frontend → API Gateway → Authentication → Business Logic → Database → Response
```

### Job Scraping Flow
```mermaid
Scheduler → Scraper → External APIs → Data Processing → Database → Matching Algorithm
```

### Authentication Flow
```mermaid
Login → Validation → JWT Token → Protected Endpoints
```

## 🗄️ Database Schema

### Core Tables
- **users**: User authentication and profiles
- **jobs**: Job listings with full metadata
- **companies**: Employer information
- **job_applications**: User application tracking
- **saved_jobs**: User job bookmarks

### Relationships
- Users have many JobApplications and SavedJobs
- Companies have many Jobs
- Jobs belong to Companies and have many Applications

## 🚀 Deployment Architecture

### Production Stack
- **Platform**: Render.com
- **Database**: PostgreSQL (persistent)
- **Caching**: Redis (memory-based)
- **File Storage**: Local filesystem (upgradeable to S3)
- **Background Jobs**: APScheduler with database persistence

### Environment Configuration
- **Development**: SQLite + local Redis
- **Production**: PostgreSQL + managed Redis
- **Environment Variables**: Secure configuration via platform dashboard

## 🔐 Security Architecture

### Authentication
- JWT tokens with configurable expiration
- Secure password hashing (bcrypt)
- Environment-based secret management

### Data Protection
- Environment variables for sensitive data
- Database connection encryption in production
- CORS configuration for frontend security

### API Security
- Rate limiting configuration
- Input validation via Pydantic
- SQL injection prevention via SQLAlchemy ORM

## 📈 Scalability Considerations

### Current Architecture Supports
- Horizontal scaling via stateless design
- Database connection pooling
- Background job processing
- Caching layer integration

### Future Enhancements
- Microservices decomposition
- Queue-based job processing (Celery/Redis)
- CDN integration for file storage
- Load balancer configuration

## 🧪 Testing Strategy

### Test Structure (Recommended)
```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for API endpoints
├── fixtures/       # Test data fixtures
└── conftest.py     # Test configuration
```

## 📊 Monitoring & Observability

### Built-in Monitoring
- Health check endpoints
- Structured logging
- Error tracking capabilities
- Performance monitoring hooks

### External Integration Ready
- Sentry for error tracking
- Custom metrics collection
- Log aggregation support

## 🔧 Development Workflow

### Local Development
1. Clone repository
2. Copy `.env.example` to `.env` with local values
3. Install dependencies: `pip install -r requirements.txt`
4. Run migrations: `alembic upgrade head`
5. Start server: `uvicorn app.main:app --reload`

### Database Migrations
1. Create migration: `alembic revision --autogenerate -m "description"`
2. Apply migration: `alembic upgrade head`
3. Rollback if needed: `alembic downgrade -1`

### Deployment Process
1. Commit changes to main branch
2. Render automatically deploys from GitHub
3. Migrations run automatically during build
4. Health check confirms successful deployment

This architecture provides a solid foundation for a production-ready job search platform with AI capabilities, automated data collection, and scalable user management.