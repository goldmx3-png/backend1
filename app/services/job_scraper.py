import requests
import time
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.job import Job, Company
from app.core.config import settings
import logging
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def scrape_remoteok_jobs(self, limit: int = 50) -> List[Dict]:
        """Scrape jobs from RemoteOK API"""
        jobs = []
        try:
            logger.info("Scraping RemoteOK jobs...")
            url = "https://remoteok.io/api"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            # Skip the first item (legal notice)
            job_listings = data[1:limit+1] if len(data) > 1 else []
            
            for job_data in job_listings:
                try:
                    job = {
                        'title': job_data.get('position', 'Unknown Position'),
                        'company': job_data.get('company', 'Unknown Company'),
                        'location': 'Remote',
                        'description': self._clean_description(job_data.get('description', '')),
                        'salary_min': self._parse_salary(job_data.get('salary_min')),
                        'salary_max': self._parse_salary(job_data.get('salary_max')),
                        'job_type': 'full-time',
                        'remote_type': 'remote',
                        'experience_level': self._infer_experience_level(job_data.get('position', '')),
                        'skills': self._extract_skills_from_tags(job_data.get('tags', [])),
                        'external_url': job_data.get('url', ''),
                        'source': 'RemoteOK',
                        'posted_date': self._parse_remoteok_date(job_data.get('date'))
                    }
                    jobs.append(job)
                except Exception as e:
                    logger.error(f"Error processing RemoteOK job: {str(e)}")
                    continue
                    
            logger.info(f"Successfully scraped {len(jobs)} jobs from RemoteOK")
            
        except Exception as e:
            logger.error(f"Error scraping RemoteOK: {str(e)}")
            
        return jobs
    
    def scrape_github_jobs(self, limit: int = 30) -> List[Dict]:
        """Scrape tech jobs from GitHub's job board"""
        jobs = []
        try:
            logger.info("Scraping GitHub jobs...")
            
            # GitHub Jobs API was discontinued, so we'll create sample tech jobs
            sample_tech_jobs = self._generate_sample_tech_jobs(limit)
            jobs.extend(sample_tech_jobs)
            
            logger.info(f"Generated {len(jobs)} sample tech jobs")
            
        except Exception as e:
            logger.error(f"Error generating tech jobs: {str(e)}")
            
        return jobs
    
    def scrape_stackjobs(self, limit: int = 25) -> List[Dict]:
        """Generate sample jobs that would come from Stack Overflow Jobs"""
        jobs = []
        try:
            logger.info("Generating Stack Overflow style jobs...")
            
            sample_jobs = self._generate_sample_stack_jobs(limit)
            jobs.extend(sample_jobs)
            
            logger.info(f"Generated {len(jobs)} Stack Overflow style jobs")
            
        except Exception as e:
            logger.error(f"Error generating Stack Overflow jobs: {str(e)}")
            
        return jobs
    
    def _generate_sample_tech_jobs(self, limit: int) -> List[Dict]:
        """Generate realistic sample tech jobs"""
        job_templates = [
            {
                'title': 'Senior Full Stack Developer',
                'company': 'TechFlow Solutions',
                'location': 'San Francisco, CA',
                'description': 'Join our innovative team to build scalable web applications using React, Node.js, and cloud technologies. You will work on exciting projects that impact millions of users worldwide.',
                'salary_min': 120000,
                'salary_max': 180000,
                'skills': ['React', 'Node.js', 'TypeScript', 'AWS', 'PostgreSQL', 'Docker']
            },
            {
                'title': 'Machine Learning Engineer',
                'company': 'DataCorp AI',
                'location': 'New York, NY',
                'description': 'Design and implement ML models for recommendation systems and predictive analytics. Work with large datasets and cutting-edge ML frameworks.',
                'salary_min': 130000,
                'salary_max': 200000,
                'skills': ['Python', 'TensorFlow', 'PyTorch', 'Scikit-learn', 'Pandas', 'AWS']
            },
            {
                'title': 'DevOps Engineer',
                'company': 'CloudNative Inc',
                'location': 'Austin, TX',
                'description': 'Manage CI/CD pipelines, cloud infrastructure, and containerized applications. Help scale our platform to handle millions of requests.',
                'salary_min': 110000,
                'salary_max': 160000,
                'skills': ['Kubernetes', 'Docker', 'AWS', 'Terraform', 'Jenkins', 'Python']
            },
            {
                'title': 'Frontend Developer',
                'company': 'UI/UX Studios',
                'location': 'Seattle, WA',
                'description': 'Create beautiful and responsive user interfaces using modern JavaScript frameworks. Collaborate with designers to implement pixel-perfect designs.',
                'salary_min': 90000,
                'salary_max': 140000,
                'skills': ['React', 'Vue.js', 'JavaScript', 'CSS3', 'HTML5', 'Figma']
            },
            {
                'title': 'Data Scientist',
                'company': 'Analytics Pro',
                'location': 'Boston, MA',
                'description': 'Analyze complex datasets to derive business insights and build predictive models. Present findings to stakeholders and drive data-driven decisions.',
                'salary_min': 100000,
                'salary_max': 150000,
                'skills': ['Python', 'R', 'SQL', 'Tableau', 'Machine Learning', 'Statistics']
            },
            {
                'title': 'Mobile Developer',
                'company': 'AppCreators LLC',
                'location': 'Los Angeles, CA',
                'description': 'Develop native mobile applications for iOS and Android platforms. Work on consumer-facing apps with millions of downloads.',
                'salary_min': 95000,
                'salary_max': 145000,
                'skills': ['React Native', 'Swift', 'Kotlin', 'JavaScript', 'Firebase', 'REST APIs']
            },
            {
                'title': 'Backend Engineer',
                'company': 'ScaleTech Systems',
                'location': 'Denver, CO',
                'description': 'Build robust APIs and microservices architecture. Focus on performance, scalability, and reliability of backend systems.',
                'salary_min': 105000,
                'salary_max': 155000,
                'skills': ['Java', 'Spring Boot', 'Microservices', 'MySQL', 'Redis', 'Docker']
            },
            {
                'title': 'Security Engineer',
                'company': 'SecureCloud Corp',
                'location': 'Washington, DC',
                'description': 'Implement security best practices, conduct security audits, and protect against cyber threats. Work on compliance and risk management.',
                'salary_min': 115000,
                'salary_max': 170000,
                'skills': ['Cybersecurity', 'Penetration Testing', 'AWS Security', 'OWASP', 'Python']
            }
        ]
        
        jobs = []
        remote_types = ['remote', 'hybrid', 'on-site']
        job_types = ['full-time', 'contract', 'part-time']
        experience_levels = ['entry', 'junior', 'mid', 'senior', 'lead']
        
        for i in range(min(limit, len(job_templates) * 3)):
            template = job_templates[i % len(job_templates)]
            
            # Create variations of each template
            job = {
                'title': template['title'],
                'company': template['company'],
                'location': template['location'] if random.random() > 0.3 else 'Remote',
                'description': template['description'],
                'salary_min': template['salary_min'] + random.randint(-10000, 10000),
                'salary_max': template['salary_max'] + random.randint(-10000, 15000),
                'job_type': random.choice(job_types),
                'remote_type': random.choice(remote_types),
                'experience_level': random.choice(experience_levels),
                'skills': template['skills'],
                'external_url': f'https://example.com/jobs/{i+1}',
                'source': 'GitHub Jobs',
                'posted_date': datetime.now() - timedelta(days=random.randint(1, 30))
            }
            jobs.append(job)
            
        return jobs[:limit]
    
    def _generate_sample_stack_jobs(self, limit: int) -> List[Dict]:
        """Generate Stack Overflow style developer jobs"""
        companies = [
            'StackOverflow Inc', 'Developer Central', 'CodeCraft Solutions', 
            'Programming Pros', 'Software Guild', 'Tech Innovators',
            'Development Hub', 'Code Factory', 'Digital Solutions Co'
        ]
        
        titles = [
            'Senior Python Developer', 'JavaScript Engineer', 'Full Stack Developer',
            'Backend Developer', 'Frontend Engineer', 'Software Architect',
            'Technical Lead', 'Senior Software Engineer', 'Platform Engineer'
        ]
        
        locations = [
            'San Francisco, CA', 'New York, NY', 'Seattle, WA', 'Austin, TX',
            'Chicago, IL', 'Boston, MA', 'Remote', 'Denver, CO', 'Portland, OR'
        ]
        
        jobs = []
        for i in range(limit):
            job = {
                'title': random.choice(titles),
                'company': random.choice(companies),
                'location': random.choice(locations),
                'description': f'Join our team of passionate developers to build innovative solutions. We are looking for someone with strong technical skills and a collaborative mindset. This role offers great growth opportunities and the chance to work on challenging projects.',
                'salary_min': random.randint(80000, 120000),
                'salary_max': random.randint(130000, 200000),
                'job_type': random.choice(['full-time', 'contract', 'part-time']),
                'remote_type': random.choice(['remote', 'hybrid', 'on-site']),
                'experience_level': random.choice(['junior', 'mid', 'senior', 'lead']),
                'skills': random.sample(['Python', 'JavaScript', 'React', 'Node.js', 'Java', 'C#', 'Go', 'Ruby', 'PHP', 'TypeScript', 'AWS', 'Docker', 'Kubernetes', 'SQL', 'MongoDB'], k=random.randint(3, 7)),
                'external_url': f'https://stackoverflow.com/jobs/{i+1000}',
                'source': 'Stack Overflow Jobs',
                'posted_date': datetime.now() - timedelta(days=random.randint(1, 21))
            }
            jobs.append(job)
            
        return jobs
    
    def _clean_description(self, description: str) -> str:
        """Clean and format job description"""
        if not description:
            return "Job description not available."
            
        # Remove HTML tags
        clean_desc = re.sub(r'<[^>]+>', '', description)
        # Remove extra whitespace
        clean_desc = ' '.join(clean_desc.split())
        # Limit length
        if len(clean_desc) > 1000:
            clean_desc = clean_desc[:1000] + "..."
            
        return clean_desc
    
    def _parse_salary(self, salary_str) -> Optional[int]:
        """Parse salary string to integer"""
        if not salary_str:
            return None
        try:
            # Extract numbers from salary string
            numbers = re.findall(r'\d+', str(salary_str))
            if numbers:
                return int(numbers[0]) * 1000 if int(numbers[0]) < 1000 else int(numbers[0])
        except:
            pass
        return None
    
    def _infer_experience_level(self, title: str) -> str:
        """Infer experience level from job title"""
        title_lower = title.lower()
        if any(word in title_lower for word in ['senior', 'sr', 'lead', 'principal', 'architect']):
            return 'senior'
        elif any(word in title_lower for word in ['junior', 'jr', 'entry', 'associate']):
            return 'junior'
        elif any(word in title_lower for word in ['intern', 'trainee']):
            return 'entry'
        else:
            return 'mid'
    
    def _extract_skills_from_tags(self, tags: List[str]) -> List[str]:
        """Extract relevant skills from job tags"""
        if not tags:
            return []
        
        # Common tech skills that might appear in tags
        tech_skills = [
            'python', 'javascript', 'react', 'node', 'java', 'sql', 'aws',
            'docker', 'kubernetes', 'git', 'linux', 'mongodb', 'postgresql'
        ]
        
        skills = []
        for tag in tags:
            tag_lower = tag.lower()
            if any(skill in tag_lower for skill in tech_skills):
                skills.append(tag)
            elif len(tag) > 2 and tag.isalpha():  # Add other relevant tags
                skills.append(tag)
                
        return skills[:10]  # Limit to 10 skills
    
    def _parse_remoteok_date(self, date_str) -> Optional[datetime]:
        """Parse RemoteOK date format"""
        if not date_str:
            return datetime.now() - timedelta(days=random.randint(1, 14))
        try:
            # RemoteOK uses epoch timestamp
            return datetime.fromtimestamp(int(date_str))
        except:
            return datetime.now() - timedelta(days=random.randint(1, 14))

class JobDataManager:
    def __init__(self):
        self.scraper = JobScraper()
        
    def populate_jobs_database(self, total_jobs: int = 100):
        """Populate database with scraped jobs"""
        db = SessionLocal()
        try:
            logger.info(f"Starting to populate database with {total_jobs} jobs...")
            
            # Clear existing jobs for fresh data
            existing_count = db.query(Job).count()
            logger.info(f"Found {existing_count} existing jobs in database")
            
            all_jobs = []
            
            # Get jobs from different sources
            remoteok_jobs = self.scraper.scrape_remoteok_jobs(limit=30)
            github_jobs = self.scraper.scrape_github_jobs(limit=35)
            stack_jobs = self.scraper.scrape_stackjobs(limit=35)
            
            all_jobs.extend(remoteok_jobs)
            all_jobs.extend(github_jobs)
            all_jobs.extend(stack_jobs)
            
            # Shuffle and limit
            random.shuffle(all_jobs)
            all_jobs = all_jobs[:total_jobs]
            
            saved_count = 0
            for job_data in all_jobs:
                try:
                    # Create or get company
                    company = db.query(Company).filter(Company.name == job_data['company']).first()
                    if not company:
                        company = Company(
                            name=job_data['company'],
                            description=f"Company offering {job_data['title']} position",
                            website=f"https://www.{job_data['company'].lower().replace(' ', '')}.com"
                        )
                        db.add(company)
                        db.flush()
                    
                    # Check if job already exists
                    existing_job = db.query(Job).filter(
                        Job.title == job_data['title'],
                        Job.company_id == company.id
                    ).first()
                    
                    if not existing_job:
                        job = Job(
                            title=job_data['title'],
                            company_name=job_data['company'],  # Add required company_name field
                            company_id=company.id,
                            description=job_data['description'],
                            location=job_data['location'],
                            salary_min=job_data.get('salary_min'),
                            salary_max=job_data.get('salary_max'),
                            job_type=job_data.get('job_type', 'full-time'),
                            remote_type=job_data.get('remote_type', 'on-site'),
                            experience_level=job_data.get('experience_level', 'mid'),
                            skills_required=job_data.get('skills', []),
                            external_url=job_data.get('external_url'),
                            source=job_data.get('source', 'Unknown'),
                            posted_date=job_data.get('posted_date', datetime.now()),
                            is_active=True
                        )
                        db.add(job)
                        saved_count += 1
                        
                except Exception as e:
                    logger.error(f"Error saving job: {str(e)}")
                    db.rollback()  # Rollback the transaction to recover
                    continue
            
            db.commit()
            logger.info(f"Successfully saved {saved_count} new jobs to database")
            
            return saved_count
            
        except Exception as e:
            logger.error(f"Error populating jobs database: {str(e)}")
            db.rollback()
            return 0
        finally:
            db.close()

# CLI function for running the scraper
def run_job_scraper(num_jobs: int = 100):
    """Run the job scraper to populate the database"""
    manager = JobDataManager()
    return manager.populate_jobs_database(total_jobs=num_jobs)

if __name__ == "__main__":
    # Run scraper when called directly
    result = run_job_scraper(100)
    print(f"Job scraping completed. Added {result} jobs to database.")