import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.job import Job, Company
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class JobScraperService:
    def __init__(self):
        self.session = SessionLocal()
        self.rate_limit = 2  # seconds between requests
    
    def scrape_indeed_jobs(self, keywords: str, location: str = "", pages: int = 5) -> List[Dict]:
        """Scrape jobs from Indeed"""
        jobs = []
        
        for page in range(pages):
            url = f"https://indeed.com/jobs?q={keywords}&l={location}&start={page * 10}"
            
            try:
                response = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    job_cards = soup.find_all('div', class_='job_seen_beacon')
                    
                    for card in job_cards:
                        job_data = self._extract_indeed_job_data(card)
                        if job_data:
                            jobs.append(job_data)
                
                time.sleep(self.rate_limit)
                
            except Exception as e:
                logger.error(f"Error scraping Indeed page {page}: {str(e)}")
                continue
        
        return jobs
    
    def scrape_remoteok_jobs(self) -> List[Dict]:
        """Scrape jobs from RemoteOK API"""
        jobs = []
        
        try:
            response = requests.get('https://remoteok.io/api')
            
            if response.status_code == 200:
                data = response.json()
                
                for job in data[1:]:  # First item is metadata
                    job_data = self._extract_remoteok_job_data(job)
                    if job_data:
                        jobs.append(job_data)
            
            time.sleep(self.rate_limit)
            
        except Exception as e:
            logger.error(f"Error scraping RemoteOK: {str(e)}")
        
        return jobs
    
    def _extract_indeed_job_data(self, card) -> Dict:
        """Extract job data from Indeed job card"""
        try:
            title_elem = card.find('h2', class_='jobTitle')
            title = title_elem.find('a').text.strip() if title_elem else "Unknown"
            
            company_elem = card.find('span', class_='companyName')
            company = company_elem.text.strip() if company_elem else "Unknown"
            
            location_elem = card.find('div', class_='companyLocation')
            location = location_elem.text.strip() if location_elem else ""
            
            summary_elem = card.find('div', class_='summary')
            description = summary_elem.text.strip() if summary_elem else ""
            
            salary_elem = card.find('span', class_='salary-snippet')
            salary_text = salary_elem.text.strip() if salary_elem else ""
            
            link_elem = title_elem.find('a') if title_elem else None
            external_url = f"https://indeed.com{link_elem['href']}" if link_elem and link_elem.get('href') else ""
            
            salary_min, salary_max = self._parse_salary(salary_text)
            
            return {
                'title': title,
                'company_name': company,
                'description': description,
                'location': location,
                'salary_min': salary_min,
                'salary_max': salary_max,
                'external_url': external_url,
                'source': 'indeed',
                'posted_date': datetime.now(),
                'job_type': 'full-time',
                'remote_type': 'hybrid' if 'remote' in location.lower() else 'on-site'
            }
            
        except Exception as e:
            logger.error(f"Error extracting Indeed job data: {str(e)}")
            return None
    
    def _extract_remoteok_job_data(self, job) -> Dict:
        """Extract job data from RemoteOK API response"""
        try:
            tags = job.get('tags', [])
            skills_required = [tag for tag in tags if isinstance(tag, str)]
            
            salary_min = job.get('salary_min')
            salary_max = job.get('salary_max')
            
            return {
                'title': job.get('position', 'Unknown'),
                'company_name': job.get('company', 'Unknown'),
                'description': job.get('description', ''),
                'location': 'Remote',
                'salary_min': salary_min,
                'salary_max': salary_max,
                'external_url': job.get('url', ''),
                'source': 'remoteok',
                'posted_date': datetime.fromtimestamp(job.get('date', 0)) if job.get('date') else datetime.now(),
                'job_type': 'full-time',
                'remote_type': 'remote',
                'skills_required': skills_required
            }
            
        except Exception as e:
            logger.error(f"Error extracting RemoteOK job data: {str(e)}")
            return None
    
    def _parse_salary(self, salary_text: str) -> tuple:
        """Parse salary range from text"""
        if not salary_text:
            return None, None
        
        # Remove common currency symbols and clean text
        clean_text = re.sub(r'[,$]', '', salary_text.lower())
        
        # Look for salary ranges
        range_pattern = r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*-\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
        range_match = re.search(range_pattern, clean_text)
        
        if range_match:
            min_sal = int(float(range_match.group(1).replace(',', '')))
            max_sal = int(float(range_match.group(2).replace(',', '')))
            
            # Convert hourly to annual (assuming 2080 hours/year)
            if 'hour' in salary_text.lower():
                min_sal *= 2080
                max_sal *= 2080
            
            return min_sal, max_sal
        
        # Look for single salary values
        single_pattern = r'(\d+(?:,\d{3})*(?:\.\d{2})?)'
        single_match = re.search(single_pattern, clean_text)
        
        if single_match:
            salary = int(float(single_match.group(1).replace(',', '')))
            
            if 'hour' in salary_text.lower():
                salary *= 2080
            
            return salary, salary
        
        return None, None
    
    def save_jobs_to_database(self, jobs: List[Dict]):
        """Save scraped jobs to database"""
        for job_data in jobs:
            try:
                # Get or create company
                company = self.session.query(Company).filter(
                    Company.name == job_data['company_name']
                ).first()
                
                if not company:
                    company = Company(name=job_data['company_name'])
                    self.session.add(company)
                    self.session.commit()
                    self.session.refresh(company)
                
                # Check if job already exists
                existing_job = self.session.query(Job).filter(
                    Job.title == job_data['title'],
                    Job.company_name == job_data['company_name'],
                    Job.external_url == job_data.get('external_url', '')
                ).first()
                
                if not existing_job:
                    job = Job(
                        title=job_data['title'],
                        company_name=job_data['company_name'],
                        description=job_data['description'],
                        location=job_data.get('location'),
                        salary_min=job_data.get('salary_min'),
                        salary_max=job_data.get('salary_max'),
                        external_url=job_data.get('external_url'),
                        source=job_data['source'],
                        posted_date=job_data.get('posted_date', datetime.now()),
                        job_type=job_data.get('job_type', 'full-time'),
                        remote_type=job_data.get('remote_type', 'on-site'),
                        skills_required=job_data.get('skills_required', []),
                        company_id=company.id
                    )
                    self.session.add(job)
                
            except Exception as e:
                logger.error(f"Error saving job to database: {str(e)}")
                self.session.rollback()
        
        try:
            self.session.commit()
        except Exception as e:
            logger.error(f"Error committing jobs to database: {str(e)}")
            self.session.rollback()
    
    def run_scraping_job(self, keywords: List[str] = None):
        """Run the complete scraping job"""
        if keywords is None:
            keywords = ["software engineer", "data scientist", "product manager", "frontend developer", "backend developer"]
        
        all_jobs = []
        
        # Scrape Indeed
        for keyword in keywords:
            indeed_jobs = self.scrape_indeed_jobs(keyword)
            all_jobs.extend(indeed_jobs)
            time.sleep(self.rate_limit)
        
        # Scrape RemoteOK
        remoteok_jobs = self.scrape_remoteok_jobs()
        all_jobs.extend(remoteok_jobs)
        
        # Save to database
        self.save_jobs_to_database(all_jobs)
        
        logger.info(f"Scraped and saved {len(all_jobs)} jobs")
        return len(all_jobs)
    
    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()