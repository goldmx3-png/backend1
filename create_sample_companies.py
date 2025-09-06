#!/usr/bin/env python3
"""
Script to create sample companies and update jobs with company information
"""
import sys
import os
import random
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.job import Job, Company
from sqlalchemy.orm import Session

def create_sample_companies():
    db = SessionLocal()
    
    companies_data = [
        {
            "name": "Darktrace",
            "industry": "Cybersecurity • AI",
            "size": "1000-5000",
            "location": "Cambridge, UK",
            "description": "Leading AI cybersecurity company protecting organizations from cyber threats."
        },
        {
            "name": "DevTools Pro",
            "industry": "Developer Tools • SaaS",
            "size": "50-200",
            "location": "Denver, CO",
            "description": "Building next-generation developer productivity tools."
        },
        {
            "name": "StackOverflow Inc",
            "industry": "Technology • Developer Community",
            "size": "200-500",
            "location": "New York, NY",
            "description": "The world's largest developer community platform."
        },
        {
            "name": "Analytics Pro",
            "industry": "Data Analytics • AI",
            "size": "100-500",
            "location": "San Francisco, CA",
            "description": "Advanced analytics and machine learning solutions for enterprises."
        },
        {
            "name": "ScaleTech Systems",
            "industry": "Cloud Infrastructure • Backend",
            "size": "500-1000",
            "location": "Seattle, WA",
            "description": "Building scalable cloud infrastructure solutions for modern applications."
        },
        {
            "name": "TechInnovate",
            "industry": "Software • Innovation",
            "size": "200-1000",
            "location": "Austin, TX",
            "description": "Innovative technology solutions for the digital age."
        },
        {
            "name": "CodeCraft Labs",
            "industry": "Software Development • Consulting",
            "size": "50-200",
            "location": "Remote",
            "description": "Premium software development and consulting services."
        },
        {
            "name": "DataFlow Inc",
            "industry": "Big Data • Analytics",
            "size": "100-500",
            "location": "Boston, MA",
            "description": "Real-time data processing and analytics platform."
        }
    ]
    
    created_companies = {}
    
    try:
        for company_data in companies_data:
            # Check if company already exists
            existing_company = db.query(Company).filter(Company.name == company_data["name"]).first()
            
            if existing_company:
                print(f"Company {company_data['name']} already exists, skipping...")
                created_companies[company_data["name"]] = existing_company
                continue
            
            # Create new company
            company = Company(
                name=company_data["name"],
                industry=company_data["industry"],
                size=company_data["size"],
                location=company_data["location"],
                description=company_data["description"]
            )
            
            db.add(company)
            created_companies[company_data["name"]] = company
            print(f"Created company: {company_data['name']}")
        
        # Commit companies first
        db.commit()
        
        # Now update jobs with company associations and application counts
        jobs = db.query(Job).all()
        
        for job in jobs:
            # Find matching company or assign random one
            if job.company_name in created_companies:
                job.company_id = created_companies[job.company_name].id
            else:
                # Assign random company if exact match not found
                random_company = random.choice(list(created_companies.values()))
                job.company_id = random_company.id
                job.company_name = random_company.name
            
            # Add realistic application counts
            job.application_count = random.randint(5, 150)
            job.view_count = random.randint(50, 500)
        
        db.commit()
        print(f"\n✅ Successfully created {len(created_companies)} companies")
        print(f"✅ Updated {len(jobs)} jobs with company associations and metrics")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating companies: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_companies()