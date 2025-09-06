#!/usr/bin/env python3
"""
Job Scraper CLI Script
Run this script to populate the database with job listings
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.job_scraper import run_job_scraper
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    parser = argparse.ArgumentParser(description='Scrape and populate job listings')
    parser.add_argument(
        '--num-jobs', 
        type=int, 
        default=100,
        help='Number of jobs to scrape (default: 100)'
    )
    
    args = parser.parse_args()
    
    print(f"🚀 Starting job scraping process...")
    print(f"📊 Target: {args.num_jobs} jobs")
    print("-" * 50)
    
    try:
        result = run_job_scraper(args.num_jobs)
        
        print("-" * 50)
        print(f"✅ Job scraping completed successfully!")
        print(f"📈 Added {result} new jobs to the database")
        
        if result > 0:
            print("\n🎉 You can now:")
            print("  • Visit http://localhost/jobs to browse jobs")
            print("  • Test the job search functionality")
            print("  • Try the job matching features")
        else:
            print("\n⚠️  No new jobs were added. This might be because:")
            print("  • Jobs already exist in the database")
            print("  • There was an issue with the scraping process")
        
    except Exception as e:
        print(f"❌ Error during job scraping: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()