"""
Job Scraping Scheduler - Industry Standard Implementation
Features:
- Interval-based job scraping
- Configurable scheduling via environment variables
- Background task processing with APScheduler
- Error handling and retry logic
- Health monitoring and metrics
- Graceful shutdown handling
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import signal
import sys
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

from app.core.config import settings
from app.services.enhanced_job_scraper import run_enhanced_job_scraper
from app.core.database import SessionLocal
from app.models.job import Job

logger = logging.getLogger(__name__)

class JobScrapingMetrics:
    """Track job scraping metrics and health"""
    
    def __init__(self):
        self.last_run: Optional[datetime] = None
        self.last_success: Optional[datetime] = None
        self.consecutive_failures = 0
        self.total_runs = 0
        self.total_jobs_scraped = 0
        self.total_jobs_saved = 0
        
    def record_run_start(self):
        """Record the start of a scraping run"""
        self.last_run = datetime.now()
        self.total_runs += 1
        
    def record_run_success(self, jobs_scraped: int, jobs_saved: int):
        """Record a successful scraping run"""
        self.last_success = datetime.now()
        self.consecutive_failures = 0
        self.total_jobs_scraped += jobs_scraped
        self.total_jobs_saved += jobs_saved
        
    def record_run_failure(self):
        """Record a failed scraping run"""
        self.consecutive_failures += 1
        
    def is_healthy(self) -> bool:
        """Check if the scraping system is healthy"""
        if not self.last_run:
            return False
            
        # Consider unhealthy if no successful run in the last 2 intervals
        max_time_since_success = timedelta(minutes=settings.SCRAPING_INTERVAL_MINUTES * 2)
        
        if self.last_success and (datetime.now() - self.last_success) <= max_time_since_success:
            return True
            
        return self.consecutive_failures < 3
    
    def get_status(self) -> Dict:
        """Get current status and metrics"""
        return {
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'last_success': self.last_success.isoformat() if self.last_success else None,
            'consecutive_failures': self.consecutive_failures,
            'total_runs': self.total_runs,
            'total_jobs_scraped': self.total_jobs_scraped,
            'total_jobs_saved': self.total_jobs_saved,
            'is_healthy': self.is_healthy(),
            'uptime_minutes': (datetime.now() - self.last_run).total_seconds() / 60 if self.last_run else 0
        }

class JobScrapingScheduler:
    """Scheduler for automated job scraping with industry best practices"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.metrics = JobScrapingMetrics()
        self._shutdown_event = asyncio.Event()
        self._setup_signal_handlers()
        
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())
            
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
    def _setup_scheduler_events(self):
        """Setup scheduler event listeners"""
        def job_listener(event):
            if event.exception:
                logger.error(f"Job {event.job_id} failed: {event.exception}")
                self.metrics.record_run_failure()
            else:
                logger.info(f"Job {event.job_id} executed successfully")
                
        self.scheduler.add_listener(job_listener, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)
        
    async def scrape_jobs_task(self):
        """Main job scraping task"""
        job_id = f"job_scraping_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            logger.info(f"Starting job scraping task: {job_id}")
            self.metrics.record_run_start()
            
            # Check if scraping is enabled
            if not settings.SCRAPING_ENABLED:
                logger.info("Job scraping is disabled via configuration")
                return
                
            # Check system health before scraping
            if self.metrics.consecutive_failures >= 5:
                logger.warning("Too many consecutive failures, skipping this run")
                await self._send_alert("Job scraping disabled due to consecutive failures")
                return
                
            # Run the enhanced job scraper
            results = await run_enhanced_job_scraper(settings.SCRAPING_MAX_JOBS_PER_RUN)
            
            # Process results
            total_scraped = results.get('total_scraped', 0)
            total_saved = results.get('total_saved', 0)
            
            self.metrics.record_run_success(total_scraped, total_saved)
            
            # Log detailed results
            logger.info(f"Job scraping completed successfully:")
            for source, count in results.items():
                if source not in ['total_scraped', 'total_saved']:
                    logger.info(f"  {source}: {count} jobs")
            logger.info(f"  Total scraped: {total_scraped}")
            logger.info(f"  Total saved: {total_saved}")
            
            # Send success notification if enabled
            if settings.ENABLE_ERROR_NOTIFICATIONS and total_saved > 0:
                await self._send_notification(
                    f"Job scraping successful: {total_saved} new jobs added",
                    level="info"
                )
                
        except Exception as e:
            logger.error(f"Job scraping task failed: {str(e)}", exc_info=True)
            self.metrics.record_run_failure()
            
            # Send error notification
            await self._send_alert(f"Job scraping failed: {str(e)}")
            
    async def _send_notification(self, message: str, level: str = "info"):
        """Send notification about scraping status"""
        try:
            if settings.SLACK_WEBHOOK_URL:
                await self._send_slack_notification(message, level)
            
            if settings.ERROR_NOTIFICATION_EMAIL and settings.SMTP_USER:
                await self._send_email_notification(message, level)
                
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            
    async def _send_alert(self, message: str):
        """Send alert for critical issues"""
        await self._send_notification(f"🚨 ALERT: {message}", level="error")
        
    async def _send_slack_notification(self, message: str, level: str):
        """Send notification to Slack"""
        import aiohttp
        
        color_map = {
            "info": "#36a64f",    # green
            "warning": "#ff9500", # orange
            "error": "#ff0000"    # red
        }
        
        payload = {
            "attachments": [
                {
                    "color": color_map.get(level, "#36a64f"),
                    "title": "Jobright AI - Job Scraping Status",
                    "text": message,
                    "timestamp": int(datetime.now().timestamp())
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            await session.post(settings.SLACK_WEBHOOK_URL, json=payload)
            
    async def _send_email_notification(self, message: str, level: str):
        """Send email notification"""
        # Import here to avoid dependency issues
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        if not settings.ERROR_NOTIFICATION_EMAIL:
            return
            
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USER
        msg['To'] = settings.ERROR_NOTIFICATION_EMAIL
        msg['Subject'] = f"Jobright AI - Job Scraping {level.upper()}"
        
        body = f"""
        Job Scraping Status Update
        
        Message: {message}
        Time: {datetime.now().isoformat()}
        Level: {level}
        
        Metrics:
        {self.metrics.get_status()}
        
        ---
        Jobright AI Job Scraping System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(settings.SMTP_USER, settings.ERROR_NOTIFICATION_EMAIL, text)
            server.quit()
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
            
    def start(self):
        """Start the job scraping scheduler"""
        if not settings.SCRAPING_ENABLED:
            logger.info("Job scraping scheduler is disabled via configuration")
            return
            
        logger.info("Starting job scraping scheduler...")
        
        # Setup scheduler events
        self._setup_scheduler_events()
        
        # Add the main scraping job
        self.scheduler.add_job(
            self.scrape_jobs_task,
            trigger=IntervalTrigger(minutes=settings.SCRAPING_INTERVAL_MINUTES),
            id='job_scraping_task',
            name='Job Scraping Task',
            max_instances=1,  # Prevent overlapping runs
            coalesce=True,    # Merge missed runs
            misfire_grace_time=300  # 5 minutes grace period
        )
        
        # Add a cleanup job to run daily at 2 AM
        self.scheduler.add_job(
            self.cleanup_old_jobs,
            trigger=CronTrigger(hour=2, minute=0),
            id='job_cleanup_task',
            name='Job Cleanup Task',
            max_instances=1
        )
        
        # Add health check job every 30 minutes
        self.scheduler.add_job(
            self.health_check_task,
            trigger=IntervalTrigger(minutes=30),
            id='health_check_task',
            name='Health Check Task',
            max_instances=1
        )
        
        # Start the scheduler
        self.scheduler.start()
        
        logger.info(f"Job scraping scheduler started with {settings.SCRAPING_INTERVAL_MINUTES} minute intervals")
        
        # Run initial scraping if configured
        if settings.SCRAPING_ENABLED:
            logger.info("Scheduling initial job scraping run...")
            self.scheduler.add_job(
                self.scrape_jobs_task,
                trigger='date',
                run_date=datetime.now() + timedelta(seconds=30),
                id='initial_scraping_task',
                name='Initial Job Scraping Task'
            )
            
    async def cleanup_old_jobs(self):
        """Clean up old job listings"""
        try:
            db = SessionLocal()
            
            # Remove jobs older than 60 days
            cutoff_date = datetime.now() - timedelta(days=60)
            
            deleted_count = db.query(Job).filter(
                Job.posted_date < cutoff_date
            ).delete(synchronize_session=False)
            
            db.commit()
            db.close()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old job listings")
                await self._send_notification(
                    f"Cleanup completed: removed {deleted_count} old jobs",
                    level="info"
                )
                
        except Exception as e:
            logger.error(f"Job cleanup failed: {str(e)}")
            await self._send_alert(f"Job cleanup failed: {str(e)}")
            
    async def health_check_task(self):
        """Perform health checks"""
        try:
            status = self.metrics.get_status()
            
            if not self.metrics.is_healthy():
                await self._send_alert(
                    f"Job scraping system unhealthy: {status['consecutive_failures']} consecutive failures"
                )
            else:
                logger.debug(f"Health check passed: {status}")
                
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            
    async def shutdown(self):
        """Gracefully shutdown the scheduler"""
        logger.info("Shutting down job scraping scheduler...")
        
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            
        self._shutdown_event.set()
        logger.info("Job scraping scheduler shut down successfully")
        
    async def run_forever(self):
        """Run the scheduler until shutdown signal"""
        self.start()
        
        try:
            # Wait for shutdown signal
            await self._shutdown_event.wait()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            await self.shutdown()
            
    def get_status(self) -> Dict:
        """Get scheduler and metrics status"""
        jobs_info = []
        
        if self.scheduler.running:
            for job in self.scheduler.get_jobs():
                jobs_info.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })
        
        return {
            'scheduler_running': self.scheduler.running,
            'jobs': jobs_info,
            'metrics': self.metrics.get_status(),
            'configuration': {
                'scraping_enabled': settings.SCRAPING_ENABLED,
                'interval_minutes': settings.SCRAPING_INTERVAL_MINUTES,
                'max_jobs_per_run': settings.SCRAPING_MAX_JOBS_PER_RUN,
                'concurrent_requests': settings.SCRAPING_CONCURRENT_REQUESTS,
                'delay_between_requests': settings.SCRAPING_DELAY_BETWEEN_REQUESTS
            }
        }

# Global scheduler instance
scheduler_instance = JobScrapingScheduler()

async def start_job_scheduler():
    """Start the job scraping scheduler"""
    await scheduler_instance.run_forever()

async def get_scheduler_status() -> Dict:
    """Get current scheduler status"""
    return scheduler_instance.get_status()

if __name__ == "__main__":
    """Run the scheduler as a standalone service"""
    import logging.config
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        logger.info("Starting Jobright AI Job Scraping Scheduler...")
        await start_job_scheduler()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler failed: {str(e)}", exc_info=True)
        sys.exit(1)