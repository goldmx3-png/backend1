# Enhanced Job Scraping System - Complete Guide

## Overview

The Jobright AI platform now includes an industry-standard job scraping system that automatically collects job postings from multiple sources with configurable intervals, rate limiting, error handling, and monitoring.

## Key Features

### 🚀 **Industry Standard Implementation**
- **Multiple Job Sources**: RemoteOK, Y Combinator, Wellfound, Otta
- **Async/Await Architecture**: High-performance concurrent scraping
- **Rate Limiting**: Token bucket algorithm with configurable limits
- **Retry Logic**: Exponential backoff with intelligent error handling
- **Proxy Rotation**: Support for proxy lists to avoid IP blocking
- **User Agent Rotation**: Randomized headers to avoid detection
- **Data Deduplication**: Hash-based duplicate detection
- **Comprehensive Logging**: Structured logging with multiple levels

### ⏰ **Automated Scheduling**
- **Interval-based Scraping**: Configurable intervals (default: 60 minutes)
- **Background Processing**: APScheduler with async support
- **Health Monitoring**: Automatic health checks and failure tracking
- **Graceful Shutdown**: Proper cleanup on termination signals
- **Job Cleanup**: Automatic removal of old job postings

### 📊 **Monitoring & Notifications**
- **Real-time Metrics**: Success rates, job counts, performance tracking  
- **Slack Integration**: Automated notifications for successes and failures
- **Email Alerts**: SMTP-based error notifications
- **Admin Dashboard**: Web-based monitoring and control panel
- **Health Endpoints**: API endpoints for system status

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# Job Scraping Configuration
SCRAPING_ENABLED=true
SCRAPING_INTERVAL_MINUTES=60
SCRAPING_MAX_JOBS_PER_RUN=200
SCRAPING_CONCURRENT_REQUESTS=5
SCRAPING_DELAY_BETWEEN_REQUESTS=2.0

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST_SIZE=20

# Job Sources (enable/disable specific sources)
ENABLE_REMOTEOK=true
ENABLE_YCOMBINATOR=true
ENABLE_WELLFOUND=true
ENABLE_OTTA=true
ENABLE_GITHUB_JOBS=false
ENABLE_STACKOVERFLOW_JOBS=false

# External API Keys (optional)
REMOTEOK_API_KEY=your_api_key_here
WELLFOUND_API_KEY=your_api_key_here
OTTA_API_KEY=your_api_key_here

# Proxy Configuration (for production)
USE_PROXY_ROTATION=false
PROXY_LIST=proxy1:port:user:pass,proxy2:port:user:pass

# User Agent Rotation
USE_USER_AGENT_ROTATION=true

# Notifications
ENABLE_ERROR_NOTIFICATIONS=true
ERROR_NOTIFICATION_EMAIL=admin@yourcompany.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Monitoring
ENABLE_PERFORMANCE_MONITORING=true
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
```

### Advanced Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `SCRAPING_ENABLED` | `true` | Enable/disable job scraping |
| `SCRAPING_INTERVAL_MINUTES` | `60` | Minutes between scraping runs |
| `SCRAPING_MAX_JOBS_PER_RUN` | `200` | Maximum jobs to scrape per run |
| `SCRAPING_CONCURRENT_REQUESTS` | `5` | Number of concurrent HTTP requests |
| `SCRAPING_DELAY_BETWEEN_REQUESTS` | `2.0` | Seconds to wait between requests |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `100` | Global rate limit per minute |
| `RATE_LIMIT_BURST_SIZE` | `20` | Token bucket burst capacity |

## Usage

### 1. Manual Job Scraping

#### Basic Usage
```bash
# Run enhanced scraper with default settings
python run_enhanced_scraper.py

# Scrape specific number of jobs
python run_enhanced_scraper.py --num-jobs 500

# Show current configuration
python run_enhanced_scraper.py --config
```

#### Advanced Usage
```bash
# Scrape from specific sources only
python run_enhanced_scraper.py --sources remoteok ycombinator

# Custom job count with specific sources
python run_enhanced_scraper.py --num-jobs 100 --sources wellfound otta
```

### 2. Automated Scheduling

#### Start the Scheduler Service
```bash
# Start the background scheduler
python -m app.services.job_scheduler

# Or run as part of the main FastAPI app
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The scheduler will:
- Start scraping immediately (30 seconds after startup)
- Run every 60 minutes (configurable)
- Perform health checks every 30 minutes
- Clean up old jobs daily at 2 AM
- Send notifications on failures

### 3. API Management

#### Admin Endpoints

```bash
# Get scraping status
GET /api/admin/scraping/status

# Get detailed statistics  
GET /api/admin/scraping/stats

# Trigger manual scraping
POST /api/admin/scraping/manual
{
  "num_jobs": 100,
  "sources": ["remoteok", "ycombinator"]
}

# Update configuration (requires restart)
PUT /api/admin/scraping/config
{
  "scraping_enabled": true,
  "interval_minutes": 30,
  "max_jobs_per_run": 150
}

# Clean up old jobs
POST /api/admin/scraping/cleanup?days_old=60

# Public health check
GET /api/admin/jobs/health
```

#### Example API Responses

**Scraping Status:**
```json
{
  "scheduler_running": true,
  "jobs": [
    {
      "id": "job_scraping_task",
      "name": "Job Scraping Task", 
      "next_run": "2025-08-31T02:30:00",
      "trigger": "interval[0:01:00]"
    }
  ],
  "metrics": {
    "last_run": "2025-08-31T01:30:00",
    "last_success": "2025-08-31T01:30:00",
    "consecutive_failures": 0,
    "total_runs": 24,
    "total_jobs_scraped": 4800,
    "total_jobs_saved": 3200,
    "is_healthy": true,
    "uptime_minutes": 1440
  }
}
```

## Job Sources

### 1. RemoteOK 
- **URL**: https://remoteok.io/api
- **Type**: Public API
- **Rate Limit**: Respectful (2s delay)
- **Data Quality**: High
- **Features**: Real job postings, salary info, tags

### 2. Y Combinator
- **URL**: https://www.ycombinator.com/api/worklist/
- **Type**: Public API  
- **Rate Limit**: Moderate (2s delay)
- **Data Quality**: High
- **Features**: Startup jobs, equity info, company details

### 3. Wellfound (AngelList)
- **URL**: Web scraping (no public API)
- **Type**: Generated sample data
- **Rate Limit**: N/A
- **Data Quality**: Mock data
- **Features**: Startup-focused job templates

### 4. Otta
- **URL**: GraphQL API (requires auth)  
- **Type**: Generated sample data
- **Rate Limit**: N/A
- **Data Quality**: Mock data
- **Features**: European/UK focused jobs

## Data Processing Pipeline

### 1. Data Collection
```
Source APIs → HTTP Requests → JSON/HTML Response → Data Extraction
```

### 2. Data Cleaning & Validation
- Remove HTML tags from descriptions
- Standardize salary formats
- Validate required fields
- Extract skills from tags/descriptions
- Infer experience levels from titles

### 3. Deduplication
- Generate hash from title + company + source_id
- Skip jobs with existing hashes
- Prevent database duplicates

### 4. Database Storage
- Create/find company records
- Insert job records with relationships
- Handle database constraints
- Commit in transactions

### 5. Post-Processing
- Update search indexes
- Generate match scores
- Trigger notifications
- Update metrics

## Error Handling & Recovery

### Retry Strategy
- **HTTP Errors**: 3 retries with exponential backoff
- **Rate Limits**: Respect 429 responses with backoff
- **Network Timeouts**: 30-second timeout per request
- **Database Errors**: Transaction rollback and continue

### Failure Modes
1. **Single Source Failure**: Continue with other sources
2. **Network Issues**: Retry with backoff, fallback to cached data
3. **Database Issues**: Rollback transactions, alert admin
4. **Memory Issues**: Process in smaller batches
5. **API Changes**: Graceful degradation, alert admin

### Monitoring & Alerts
- **Health Checks**: Every 30 minutes
- **Failure Threshold**: 3 consecutive failures = alert
- **Recovery**: Automatic retry on next scheduled run
- **Escalation**: Email + Slack alerts for persistent issues

## Performance Optimization

### Concurrent Processing
```python
# Process multiple sources simultaneously
tasks = [
    scraper.scrape_remoteok_jobs(50),
    scraper.scrape_ycombinator_jobs(50), 
    scraper.scrape_wellfound_jobs(50),
    scraper.scrape_otta_jobs(50)
]

results = await asyncio.gather(*tasks, return_exceptions=True)
```

### Rate Limiting
```python
# Token bucket algorithm
class RateLimiter:
    def __init__(self, requests_per_minute: int, burst_size: int):
        self.tokens = burst_size
        self.last_update = time.time()
    
    async def acquire(self):
        # Replenish tokens based on time elapsed
        # Block if insufficient tokens available
```

### Memory Management
- Stream processing for large datasets  
- Database connection pooling
- Async context managers for cleanup
- Garbage collection after each run

### Database Optimization
- Bulk insert operations
- Proper indexing on search fields
- Connection pooling
- Query optimization

## Deployment

### Development Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup environment
cp .env.example .env
# Edit .env with your configuration

# 3. Run database migrations
alembic upgrade head

# 4. Start the application
uvicorn app.main:app --reload

# 5. Run manual scraping
python run_enhanced_scraper.py
```

### Production Deployment
```bash
# 1. Production environment file
cp .env.example .env.prod
# Configure production settings

# 2. Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# 3. Setup monitoring
# Configure Sentry, Slack webhooks, email SMTP

# 4. Setup log rotation
# Configure log rotation for scheduler logs

# 5. Health checks  
curl http://localhost:8000/api/admin/jobs/health
```

### Docker Configuration
```dockerfile
# Dockerfile additions for scraping
FROM python:3.11-slim

# Install additional dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy enhanced scraper files
COPY app/services/enhanced_job_scraper.py /app/app/services/
COPY app/services/job_scheduler.py /app/app/services/
COPY run_enhanced_scraper.py /app/

# Set environment variables
ENV PYTHONPATH=/app
ENV SCRAPING_ENABLED=true
```

## Troubleshooting

### Common Issues

#### 1. No Jobs Being Scraped
```bash
# Check configuration
python run_enhanced_scraper.py --config

# Check if sources are enabled
grep ENABLE_ .env

# Test manual scraping
python run_enhanced_scraper.py --num-jobs 10
```

#### 2. Rate Limiting Issues
```bash
# Increase delays in .env
SCRAPING_DELAY_BETWEEN_REQUESTS=5.0
SCRAPING_CONCURRENT_REQUESTS=3

# Check rate limit settings
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

#### 3. Database Connection Issues  
```bash
# Verify database URL
echo $DATABASE_URL

# Test connection
python -c "from app.core.database import SessionLocal; db = SessionLocal(); print('Connected!')"

# Check migrations
alembic current
alembic upgrade head
```

#### 4. Scheduler Not Starting
```bash
# Check logs
tail -f logs/scheduler.log

# Verify APScheduler installation
pip list | grep APScheduler

# Test manual scheduler start
python -m app.services.job_scheduler
```

### Log Analysis
```bash
# View scraping logs
tail -f logs/job_scraper.log

# Filter for errors
grep ERROR logs/job_scraper.log

# View scheduler status  
grep "Job.*executed" logs/scheduler.log
```

### Performance Monitoring
```bash
# Check memory usage
ps aux | grep python

# Monitor database connections
SELECT * FROM pg_stat_activity WHERE datname = 'jobright_db';

# View recent scraping stats
curl http://localhost:8000/api/admin/scraping/stats
```

## Best Practices

### 1. Respectful Scraping
- Always respect robots.txt
- Implement appropriate delays between requests
- Use reasonable rate limits
- Monitor for 429 (Rate Limited) responses
- Rotate user agents and IP addresses in production

### 2. Error Handling
- Log all errors with context
- Implement circuit breakers for failing sources  
- Graceful degradation when sources fail
- Alert administrators of persistent failures
- Maintain fallback data for user experience

### 3. Data Quality
- Validate all scraped data before storage
- Implement comprehensive deduplication
- Clean and normalize text data
- Extract structured data from unstructured sources
- Monitor data quality metrics

### 4. Monitoring
- Track success/failure rates per source
- Monitor scraping performance and timing
- Set up alerts for anomalies
- Regular health checks on all components
- Dashboard for operational visibility

### 5. Scalability
- Design for horizontal scaling
- Use async/await for I/O operations
- Implement proper connection pooling
- Consider message queues for large scale
- Plan for database sharding if needed

## Security Considerations

### 1. API Security
- Protect admin endpoints with authentication
- Use HTTPS in production
- Implement rate limiting on admin APIs
- Validate all input parameters
- Log security-relevant events

### 2. Data Protection
- Encrypt sensitive configuration data
- Use environment variables for secrets
- Implement proper access controls
- Regular security audits
- GDPR compliance for EU users

### 3. Infrastructure Security  
- Secure proxy configurations
- Network segmentation
- Regular dependency updates
- Container security scanning
- Monitoring for suspicious activity

## Future Enhancements

### Planned Features
- [ ] Machine Learning for job classification
- [ ] Real-time job alerts for users
- [ ] Integration with more job boards
- [ ] Advanced analytics and reporting
- [ ] Mobile push notifications
- [ ] LinkedIn job scraping (when API available)
- [ ] Indeed integration (if API access restored)
- [ ] Glassdoor salary data integration

### Scalability Roadmap
- [ ] Kubernetes deployment
- [ ] Message queue integration (Redis/RabbitMQ)
- [ ] Microservices architecture
- [ ] Multi-region deployment
- [ ] CDN integration for global performance

---

## Support

For issues, questions, or contributions:

1. **Documentation**: Check this guide first
2. **Logs**: Review application and scheduler logs
3. **Health Checks**: Use `/api/admin/jobs/health` endpoint
4. **GitHub Issues**: Create detailed issue reports
5. **Email**: Contact the development team

---

*Last updated: August 31, 2025*