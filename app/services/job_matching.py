import numpy as np
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.models.job import Job
from app.models.user import User
from app.core.database import SessionLocal
import logging
import re
from collections import Counter
import spacy

logger = logging.getLogger(__name__)

class JobMatchingService:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        
        # Weight factors for different matching criteria
        self.weights = {
            'skills': 0.4,
            'experience': 0.25,
            'location': 0.15,
            'job_type': 0.1,
            'remote_type': 0.1
        }
        
    def calculate_job_match_score(self, user: User, job: Job) -> Dict:
        """Calculate comprehensive match score between user and job"""
        scores = {}
        
        # Skills matching (most important factor)
        scores['skills'] = self._calculate_skills_match(user.skills or [], job.skills_required or [])
        
        # Experience level matching
        scores['experience'] = self._calculate_experience_match(user.experience_years, job.experience_level)
        
        # Location preference matching
        scores['location'] = self._calculate_location_match(user.location, job.location, job.remote_type)
        
        # Job type preferences
        scores['job_type'] = self._calculate_job_type_match(user.preferred_job_types or [], job.job_type)
        
        # Remote type preferences
        scores['remote_type'] = self._calculate_remote_type_match(user.preferred_remote_types or [], job.remote_type)
        
        # Salary expectations
        scores['salary'] = self._calculate_salary_match(user.salary_expectation, job.salary_min, job.salary_max)
        
        # Calculate overall weighted score
        overall_score = (
            scores['skills'] * self.weights['skills'] +
            scores['experience'] * self.weights['experience'] +
            scores['location'] * self.weights['location'] +
            scores['job_type'] * self.weights['job_type'] +
            scores['remote_type'] * self.weights['remote_type']
        )
        
        return {
            'overall_score': round(min(overall_score * 100, 100), 1),  # Convert to percentage, max 100%
            'detailed_scores': {k: round(v * 100, 1) for k, v in scores.items()},
            'match_reasons': self._generate_match_reasons(scores, user, job),
            'improvement_suggestions': self._generate_improvement_suggestions(scores, user, job)
        }
    
    def get_matched_jobs(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get jobs ranked by match score for a specific user"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return []
            
            # Get active jobs
            jobs = db.query(Job).filter(Job.is_active == True).limit(100).all()
            
            matched_jobs = []
            for job in jobs:
                match_data = self.calculate_job_match_score(user, job)
                
                job_dict = {
                    'id': job.id,
                    'title': job.title,
                    'company_name': job.company_name,
                    'location': job.location,
                    'description': job.description[:200] + "..." if len(job.description) > 200 else job.description,
                    'salary_min': job.salary_min,
                    'salary_max': job.salary_max,
                    'job_type': job.job_type,
                    'remote_type': job.remote_type,
                    'experience_level': job.experience_level,
                    'skills_required': job.skills_required,
                    'match_score': match_data['overall_score'],
                    'match_details': match_data['detailed_scores'],
                    'match_reasons': match_data['match_reasons'],
                    'improvement_suggestions': match_data['improvement_suggestions']
                }
                matched_jobs.append(job_dict)
            
            # Sort by match score (highest first)
            matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)
            
            return matched_jobs[:limit]
            
        except Exception as e:
            logger.error(f"Error getting matched jobs: {str(e)}")
            return []
        finally:
            db.close()
    
    def _calculate_skills_match(self, user_skills: List[str], job_skills: List[str]) -> float:
        """Calculate skills matching score"""
        if not user_skills or not job_skills:
            return 0.0
        
        # Normalize skills (lowercase, remove special chars)
        user_skills_norm = [self._normalize_skill(skill) for skill in user_skills]
        job_skills_norm = [self._normalize_skill(skill) for skill in job_skills]
        
        # Direct matches
        matches = len(set(user_skills_norm) & set(job_skills_norm))
        
        # Fuzzy matching for similar skills
        fuzzy_matches = 0
        for user_skill in user_skills_norm:
            for job_skill in job_skills_norm:
                if user_skill not in job_skills_norm and self._skills_similarity(user_skill, job_skill) > 0.8:
                    fuzzy_matches += 0.5  # Partial credit for similar skills
        
        total_matches = matches + fuzzy_matches
        max_possible_matches = min(len(user_skills_norm), len(job_skills_norm))
        
        if max_possible_matches == 0:
            return 0.0
        
        score = total_matches / len(job_skills_norm)  # Based on job requirements
        return min(score, 1.0)
    
    def _calculate_experience_match(self, user_experience: Optional[int], job_experience_level: Optional[str]) -> float:
        """Calculate experience level matching"""
        if not user_experience or not job_experience_level:
            return 0.5  # Neutral score if info missing
        
        # Map experience levels to years
        experience_mapping = {
            'entry': (0, 1),
            'junior': (1, 3),
            'mid': (3, 7),
            'senior': (7, 12),
            'lead': (10, 20),
            'principal': (12, 25)
        }
        
        job_exp_range = experience_mapping.get(job_experience_level.lower(), (3, 7))
        
        # Calculate how well user's experience fits the job requirements
        if job_exp_range[0] <= user_experience <= job_exp_range[1]:
            return 1.0  # Perfect match
        elif user_experience < job_exp_range[0]:
            # Under-qualified
            gap = job_exp_range[0] - user_experience
            return max(0.2, 1 - (gap / 5))  # Penalty for being under-qualified
        else:
            # Over-qualified (less penalty)
            gap = user_experience - job_exp_range[1]
            return max(0.6, 1 - (gap / 10))
    
    def _calculate_location_match(self, user_location: Optional[str], job_location: Optional[str], remote_type: Optional[str]) -> float:
        """Calculate location preference matching"""
        if remote_type and remote_type.lower() == 'remote':
            return 1.0  # Perfect for remote jobs
        
        if not user_location or not job_location:
            return 0.5  # Neutral if location info missing
        
        user_loc_norm = user_location.lower().strip()
        job_loc_norm = job_location.lower().strip()
        
        # Direct city/state match
        if user_loc_norm in job_loc_norm or job_loc_norm in user_loc_norm:
            return 1.0
        
        # Same state
        if self._extract_state(user_location) == self._extract_state(job_location):
            return 0.7
        
        # Different locations
        return 0.3 if remote_type == 'hybrid' else 0.1
    
    def _calculate_job_type_match(self, user_preferences: List[str], job_type: Optional[str]) -> float:
        """Calculate job type preference matching"""
        if not user_preferences or not job_type:
            return 0.5  # Neutral if no preferences
        
        job_type_norm = job_type.lower().replace('-', '').replace('_', '')
        user_prefs_norm = [pref.lower().replace('-', '').replace('_', '') for pref in user_preferences]
        
        return 1.0 if job_type_norm in user_prefs_norm else 0.2
    
    def _calculate_remote_type_match(self, user_preferences: List[str], remote_type: Optional[str]) -> float:
        """Calculate remote type preference matching"""
        if not user_preferences or not remote_type:
            return 0.5
        
        remote_norm = remote_type.lower().replace('-', '')
        user_prefs_norm = [pref.lower().replace('-', '') for pref in user_preferences]
        
        return 1.0 if remote_norm in user_prefs_norm else 0.3
    
    def _calculate_salary_match(self, user_expectation: Optional[int], job_min: Optional[int], job_max: Optional[int]) -> float:
        """Calculate salary expectation matching"""
        if not user_expectation:
            return 0.5  # Neutral if no salary expectation
        
        if not job_min and not job_max:
            return 0.5  # Neutral if no salary info
        
        job_avg = ((job_min or 0) + (job_max or 200000)) / 2
        
        if job_avg >= user_expectation:
            return 1.0  # Meets or exceeds expectations
        else:
            # Calculate how far below expectations
            gap_percentage = (user_expectation - job_avg) / user_expectation
            return max(0.0, 1 - gap_percentage)
    
    def _normalize_skill(self, skill: str) -> str:
        """Normalize skill for comparison"""
        return re.sub(r'[^\w\s]', '', skill.lower().strip())
    
    def _skills_similarity(self, skill1: str, skill2: str) -> float:
        """Calculate similarity between two skills"""
        # Simple string similarity for now
        # Could be enhanced with more sophisticated NLP
        if skill1 == skill2:
            return 1.0
        
        # Check if one skill contains the other
        if skill1 in skill2 or skill2 in skill1:
            return 0.8
        
        # Basic character overlap
        common_chars = set(skill1) & set(skill2)
        return len(common_chars) / max(len(skill1), len(skill2))
    
    def _extract_state(self, location: str) -> Optional[str]:
        """Extract state from location string"""
        if not location:
            return None
        
        # Common US state abbreviations
        states = {
            'ca': 'california', 'ny': 'new york', 'tx': 'texas', 'fl': 'florida',
            'wa': 'washington', 'il': 'illinois', 'pa': 'pennsylvania', 'oh': 'ohio',
            'ga': 'georgia', 'nc': 'north carolina', 'mi': 'michigan', 'nj': 'new jersey'
        }
        
        loc_parts = location.lower().split(',')
        if len(loc_parts) >= 2:
            state_part = loc_parts[-1].strip()
            if len(state_part) == 2 and state_part in states:
                return states[state_part]
            return state_part
        
        return None
    
    def _generate_match_reasons(self, scores: Dict[str, float], user: User, job: Job) -> List[str]:
        """Generate human-readable reasons for the match"""
        reasons = []
        
        if scores['skills'] > 0.7:
            reasons.append(f"Strong skills match - you have {len(set(user.skills or []) & set(job.skills_required or []))} required skills")
        
        if scores['experience'] > 0.8:
            reasons.append("Your experience level is perfect for this role")
        elif scores['experience'] > 0.6:
            reasons.append("Your experience level is well-suited for this role")
        
        if scores['location'] > 0.9:
            reasons.append("Great location match")
        
        if scores['salary'] > 0.8:
            reasons.append("Salary meets your expectations")
        
        if job.remote_type == 'remote':
            reasons.append("Fully remote position")
        
        return reasons
    
    def _generate_improvement_suggestions(self, scores: Dict[str, float], user: User, job: Job) -> List[str]:
        """Generate suggestions to improve match score"""
        suggestions = []
        
        if scores['skills'] < 0.5:
            missing_skills = set(job.skills_required or []) - set(user.skills or [])
            if missing_skills:
                suggestions.append(f"Consider learning: {', '.join(list(missing_skills)[:3])}")
        
        if scores['experience'] < 0.5:
            suggestions.append("Gain more experience in relevant areas")
        
        if scores['location'] < 0.3 and job.remote_type != 'remote':
            suggestions.append("Consider relocating or look for remote opportunities")
        
        return suggestions

# Utility functions for API endpoints
def get_job_recommendations(user_id: int, limit: int = 20) -> List[Dict]:
    """Get personalized job recommendations for a user"""
    matching_service = JobMatchingService()
    return matching_service.get_matched_jobs(user_id, limit)

def calculate_match_score(user_id: int, job_id: int) -> Dict:
    """Calculate match score between specific user and job"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not user or not job:
            return {'error': 'User or job not found'}
        
        matching_service = JobMatchingService()
        return matching_service.calculate_job_match_score(user, job)
        
    finally:
        db.close()