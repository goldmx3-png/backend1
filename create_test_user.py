#!/usr/bin/env python3
"""
Create a test user with sample data for testing the job matching system
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import SessionLocal
from app.models.user import User
from passlib.context import CryptContext
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_user():
    """Create a test user with sample profile data"""
    db = SessionLocal()
    try:
        # Check if test user already exists
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if existing_user:
            logger.info("Test user already exists, updating profile...")
            user = existing_user
        else:
            # Create new test user
            logger.info("Creating new test user...")
            hashed_password = pwd_context.hash("testpass123")
            user = User(
                email="test@example.com",
                full_name="Test User",
                hashed_password=hashed_password,
                is_active=True
            )
            db.add(user)
            db.flush()  # Get the ID
        
        # Update profile with sample data for testing job matching
        user.job_title = "Senior Software Engineer"
        user.experience_years = 5
        user.experience_level = "senior"
        user.location = "San Francisco, CA"
        user.salary_expectation = 140000
        user.skills = [
            "Python", "JavaScript", "React", "Node.js", "PostgreSQL", 
            "AWS", "Docker", "Kubernetes", "Machine Learning", "API Design"
        ]
        user.preferred_job_types = ["full-time", "contract"]
        user.preferred_remote_types = ["remote", "hybrid"]
        user.profile_summary = "Experienced software engineer with expertise in full-stack development, cloud technologies, and machine learning. Passionate about building scalable applications and leading engineering teams."
        
        db.commit()
        
        logger.info(f"✅ Test user created/updated successfully!")
        logger.info(f"📧 Email: {user.email}")
        logger.info(f"🔑 Password: testpass123")
        logger.info(f"👤 ID: {user.id}")
        logger.info(f"🎯 Skills: {user.skills}")
        logger.info(f"💼 Experience: {user.experience_years} years ({user.experience_level})")
        logger.info(f"📍 Location: {user.location}")
        logger.info(f"💰 Salary Expectation: ${user.salary_expectation:,}")
        
        return user
        
    except Exception as e:
        logger.error(f"Error creating test user: {str(e)}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Creating test user for job matching system...")
    print("-" * 50)
    
    user = create_test_user()
    
    if user:
        print("-" * 50)
        print("🎉 Test user setup completed!")
        print("\n📝 You can now:")
        print("  • Login with email: test@example.com")
        print("  • Password: testpass123")
        print("  • Visit http://localhost/dashboard to see job recommendations")
        print("  • Test the job matching algorithm")
    else:
        print("❌ Failed to create test user")
        sys.exit(1)