#!/usr/bin/env python3
"""
Enhanced Job Scraper CLI Script
Run this script to populate the database with jobs from multiple sources using the enhanced scraper
"""

import asyncio
import sys
import os
import argparse
import logging

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.enhanced_job_scraper import run_enhanced_job_scraper
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    parser = argparse.ArgumentParser(description='Enhanced job scraper with multiple sources')
    parser.add_argument(
        '--num-jobs', 
        type=int, 
        default=settings.SCRAPING_MAX_JOBS_PER_RUN,
        help=f'Number of jobs to scrape (default: {settings.SCRAPING_MAX_JOBS_PER_RUN})'
    )
    parser.add_argument(
        '--sources',
        nargs='*',
        choices=['remoteok', 'ycombinator', 'wellfound', 'otta'],
        help='Specific sources to scrape from (default: all enabled sources)'
    )
    parser.add_argument(
        '--config',
        action='store_true',
        help='Show current configuration'
    )
    
    args = parser.parse_args()
    
    if args.config:
        print("📋 Current Scraping Configuration:")
        print(f"  Scraping Enabled: {settings.SCRAPING_ENABLED}")
        print(f"  Interval: {settings.SCRAPING_INTERVAL_MINUTES} minutes")
        print(f"  Max Jobs Per Run: {settings.SCRAPING_MAX_JOBS_PER_RUN}")
        print(f"  Concurrent Requests: {settings.SCRAPING_CONCURRENT_REQUESTS}")
        print(f"  Delay Between Requests: {settings.SCRAPING_DELAY_BETWEEN_REQUESTS}s")
        print(f"  Sources Enabled:")
        print(f"    RemoteOK: {settings.ENABLE_REMOTEOK}")
        print(f"    Y Combinator: {settings.ENABLE_YCOMBINATOR}")
        print(f"    Wellfound: {settings.ENABLE_WELLFOUND}")
        print(f"    Otta: {settings.ENABLE_OTTA}")
        print(f"  Rate Limiting: {settings.RATE_LIMIT_REQUESTS_PER_MINUTE} req/min")
        return
    
    if not settings.SCRAPING_ENABLED:
        print("❌ Scraping is disabled in configuration")
        print("   Set SCRAPING_ENABLED=true in your .env file to enable")
        sys.exit(1)
    
    print(f"🚀 Starting enhanced job scraping...")
    print(f"📊 Target: {args.num_jobs} jobs")
    print(f"🔄 Using {settings.SCRAPING_CONCURRENT_REQUESTS} concurrent requests")
    print(f"⏱️  Rate limit: {settings.RATE_LIMIT_REQUESTS_PER_MINUTE} req/min")
    if args.sources:
        print(f"🎯 Sources: {', '.join(args.sources)}")
    print("-" * 60)
    
    async def scrape():
        try:
            results = await run_enhanced_job_scraper(args.num_jobs)
            
            print("-" * 60)
            print(f"✅ Enhanced job scraping completed!")
            print(f"📈 Results by source:")
            
            total_scraped = 0
            total_saved = 0
            
            for source, count in results.items():
                if source == 'total_scraped':
                    total_scraped = count
                elif source == 'total_saved':
                    total_saved = count
                else:
                    print(f"  📍 {source}: {count} jobs")
            
            print(f"\n📊 Summary:")
            print(f"  Total scraped: {total_scraped} jobs")
            print(f"  Total saved: {total_saved} jobs")
            print(f"  Duplicates filtered: {total_scraped - total_saved} jobs")
            
            if total_saved > 0:
                print(f"\n🎉 Success! You can now:")
                print(f"  • Visit the frontend to browse {total_saved} new jobs")
                print(f"  • Test job search and filtering")
                print(f"  • Try personalized job recommendations")
            else:
                print(f"\n⚠️  No new jobs were saved:")
                print(f"  • Jobs may already exist in database")
                print(f"  • All scraped jobs may have been duplicates")
                print(f"  • Check source configurations")
            
            return total_saved
            
        except Exception as e:
            print(f"❌ Enhanced scraping failed: {str(e)}")
            logging.error(f"Scraping error: {str(e)}", exc_info=True)
            sys.exit(1)
    
    try:
        result = asyncio.run(scrape())
        
        if result > 0:
            print(f"\n🔄 To run automatic scraping:")
            print(f"  python -m app.services.job_scheduler")
            print(f"\n⚙️  To configure scraping:")
            print(f"  Edit your .env file or use environment variables")
            print(f"  Run: python run_enhanced_scraper.py --config")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()