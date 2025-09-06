
#!/usr/bin/env python3
"""
Script to create test users for Jobright AI
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def create_test_users():
    db = SessionLocal()
    
    # Test users data
    test_users = [
        {
            "email": "test@jobright.ai",
            "password": "password123",
            "full_name": "Test User",
            "job_title": "Software Engineer",
            "experience_level": "mid",
            "location": "San Francisco, CA",
            "skills": ["Python", "JavaScript", "React", "FastAPI", "PostgreSQL"],
            "job_preferences": {
                "remote_type": "remote",
                "salary_min": 80000,
                "salary_max": 120000,
                "job_types": ["full-time"]
            },
            "profile_summary": "Experienced software engineer with expertise in full-stack development."
        },
        {
            "email": "admin@jobright.ai", 
            "password": "admin123",
            "full_name": "Admin User",
            "job_title": "Product Manager",
            "experience_level": "senior",
            "location": "New York, NY",
            "skills": ["Product Management", "Strategy", "Analytics", "Leadership"],
            "job_preferences": {
                "remote_type": "hybrid",
                "salary_min": 100000,
                "salary_max": 150000,
                "job_types": ["full-time"]
            },
            "profile_summary": "Senior product manager with 8+ years of experience in tech companies."
        },
        {
            "email": "demo@jobright.ai",
            "password": "demo123", 
            "full_name": "Demo User",
            "job_title": "Data Scientist",
            "experience_level": "junior",
            "location": "Austin, TX",
            "skills": ["Python", "Machine Learning", "SQL", "Pandas", "scikit-learn"],
            "job_preferences": {
                "remote_type": "on-site",
                "salary_min": 70000,
                "salary_max": 95000,
                "job_types": ["full-time", "contract"]
            },
            "profile_summary": "Junior data scientist passionate about machine learning and AI."
        }
    ]
    
    created_users = []
    
    for user_data in test_users:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        
        if existing_user:
            print(f"User {user_data['email']} already exists, skipping...")
            continue
            
        # Create new user
        hashed_password = get_password_hash(user_data["password"])
        
        db_user = User(
            email=user_data["email"],
            hashed_password=hashed_password,
            full_name=user_data["full_name"],
            job_title=user_data.get("job_title"),
            experience_level=user_data.get("experience_level"),
            location=user_data.get("location"),
            skills=user_data.get("skills"),
            job_preferences=user_data.get("job_preferences"),
            profile_summary=user_data.get("profile_summary"),
            is_active=True,
            is_verified=True
        )
        
        db.add(db_user)
        created_users.append(user_data["email"])
    
    try:
        db.commit()
        print(f"✅ Successfully created {len(created_users)} test users:")
        for email in created_users:
            print(f"   - {email}")
            
        print("\n🔑 Test User Credentials:")
        for user_data in test_users:
            print(f"   Email: {user_data['email']}")
            print(f"   Password: {user_data['password']}")
            print(f"   Name: {user_data['full_name']}")
            print()
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating users: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()