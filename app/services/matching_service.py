from typing import List, Dict, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.job import Job
import logging

logger = logging.getLogger(__name__)

class JobMatchingService:
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        self.skills_weight = 0.4
        self.experience_weight = 0.3
        self.location_weight = 0.2
        self.description_weight = 0.1
    
    def calculate_job_match_score(self, user: User, job: Job) -> Dict:
        """Calculate comprehensive job match score for a user"""
        try:
            # Initialize scores
            skills_score = self._calculate_skills_match(user, job)
            experience_score = self._calculate_experience_match(user, job)
            location_score = self._calculate_location_match(user, job)
            description_score = self._calculate_description_match(user, job)
            
            # Calculate weighted overall score
            overall_score = (
                skills_score * self.skills_weight +
                experience_score * self.experience_weight +
                location_score * self.location_weight +
                description_score * self.description_weight
            )
            
            # Generate match reasons
            match_reasons = self._generate_match_reasons(
                user, job, skills_score, experience_score, location_score
            )
            
            return {
                'overall_score': round(overall_score * 100, 1),
                'skills_score': round(skills_score * 100, 1),
                'experience_score': round(experience_score * 100, 1),
                'location_score': round(location_score * 100, 1),
                'description_score': round(description_score * 100, 1),
                'match_reasons': match_reasons,
                'job_id': job.id,
                'user_id': user.id
            }
            
        except Exception as e:
            logger.error(f"Error calculating job match score: {str(e)}")
            return {
                'overall_score': 0.0,
                'skills_score': 0.0,
                'experience_score': 0.0,
                'location_score': 0.0,
                'description_score': 0.0,
                'match_reasons': ["Error calculating match"],
                'job_id': job.id,
                'user_id': user.id
            }
    
    def _calculate_skills_match(self, user: User, job: Job) -> float:
        """Calculate skills-based matching score"""
        if not user.skills or not job.skills_required:
            return 0.5  # Neutral score when no skills data
        
        user_skills = set([skill.lower().strip() for skill in user.skills if skill])
        job_skills = set([skill.lower().strip() for skill in job.skills_required if skill])
        
        if not job_skills:
            return 0.5
        
        # Calculate intersection and union
        common_skills = user_skills.intersection(job_skills)
        union_skills = user_skills.union(job_skills)
        
        if not union_skills:
            return 0.5
        
        # Jaccard similarity with bonus for high overlap
        jaccard_score = len(common_skills) / len(job_skills)
        
        # Bonus for having more skills than required
        skill_coverage = len(common_skills) / len(job_skills)
        skill_breadth = min(len(user_skills) / len(job_skills), 1.5) / 1.5
        
        return min(jaccard_score + (skill_breadth * 0.2), 1.0)
    
    def _calculate_experience_match(self, user: User, job: Job) -> float:
        """Calculate experience level matching score"""
        if not user.experience_level or not job.experience_level:
            return 0.7  # Neutral score when no experience data
        
        experience_mapping = {
            'entry': 1,
            'junior': 2,
            'mid': 3,
            'senior': 4,
            'lead': 5,
            'principal': 6
        }
        
        user_level = experience_mapping.get(user.experience_level.lower(), 3)
        job_level = experience_mapping.get(job.experience_level.lower(), 3)
        
        # Perfect match gets 1.0, decreasing score for larger gaps
        level_diff = abs(user_level - job_level)
        
        if level_diff == 0:
            return 1.0
        elif level_diff == 1:
            return 0.8
        elif level_diff == 2:
            return 0.6
        else:
            return 0.3
    
    def _calculate_location_match(self, user: User, job: Job) -> float:
        """Calculate location-based matching score"""
        if not user.location or not job.location:
            return 0.7  # Neutral score when no location data
        
        user_location = user.location.lower().strip()
        job_location = job.location.lower().strip()
        
        # Remote jobs are good for everyone
        if 'remote' in job_location:
            return 1.0
        
        # Exact location match
        if user_location == job_location:
            return 1.0
        
        # Check for city/state matches
        user_parts = user_location.split(',')
        job_parts = job_location.split(',')
        
        # Same city
        if len(user_parts) > 0 and len(job_parts) > 0:
            if user_parts[0].strip() == job_parts[0].strip():
                return 0.9
        
        # Same state/region
        if len(user_parts) > 1 and len(job_parts) > 1:
            if user_parts[-1].strip() == job_parts[-1].strip():
                return 0.6
        
        return 0.3
    
    def _calculate_description_match(self, user: User, job: Job) -> float:
        """Calculate job description similarity to user profile"""
        try:
            if not user.profile_summary or not job.description:
                return 0.5
            
            # Combine user information
            user_text = f"{user.profile_summary} {' '.join(user.skills or [])}"
            job_text = f"{job.description} {job.title}"
            
            # Calculate TF-IDF similarity
            documents = [user_text, job_text]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(documents)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return min(max(similarity, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating description match: {str(e)}")
            return 0.5
    
    def _generate_match_reasons(self, user: User, job: Job, skills_score: float, 
                               experience_score: float, location_score: float) -> List[str]:
        """Generate human-readable reasons for the match score"""
        reasons = []
        
        # Skills reasons
        if skills_score > 0.8:
            reasons.append("Strong skills alignment with job requirements")
        elif skills_score > 0.6:
            reasons.append("Good skills match with some overlap")
        elif skills_score < 0.4:
            reasons.append("Limited skills overlap with requirements")
        
        # Experience reasons
        if experience_score > 0.9:
            reasons.append("Perfect experience level match")
        elif experience_score > 0.7:
            reasons.append("Compatible experience level")
        elif experience_score < 0.5:
            reasons.append("Experience level may not align perfectly")
        
        # Location reasons
        if location_score > 0.9:
            reasons.append("Excellent location match")
        elif location_score > 0.7:
            reasons.append("Good location compatibility")
        elif location_score < 0.5:
            reasons.append("Location may require relocation or remote work")
        
        # Additional contextual reasons
        if user.skills and job.skills_required:
            common_skills = set([s.lower() for s in user.skills]).intersection(
                set([s.lower() for s in job.skills_required])
            )
            if common_skills:
                key_skills = list(common_skills)[:3]
                reasons.append(f"Matching skills: {', '.join(key_skills)}")
        
        return reasons[:5]  # Return top 5 reasons
    
    def get_job_recommendations(self, user: User, jobs: List[Job], limit: int = 20) -> List[Dict]:
        """Get ranked job recommendations for a user"""
        recommendations = []
        
        for job in jobs:
            match_data = self.calculate_job_match_score(user, job)
            match_data['job'] = job
            recommendations.append(match_data)
        
        # Sort by overall score
        recommendations.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return recommendations[:limit]
    
    def get_users_for_job(self, job: Job, users: List[User], limit: int = 20) -> List[Dict]:
        """Get ranked user matches for a specific job"""
        matches = []
        
        for user in users:
            match_data = self.calculate_job_match_score(user, job)
            match_data['user'] = user
            matches.append(match_data)
        
        # Sort by overall score
        matches.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return matches[:limit]
    
    def batch_calculate_matches(self, user_ids: List[int], job_ids: List[int], 
                               session: Session) -> List[Dict]:
        """Calculate matches for multiple users and jobs in batch"""
        results = []
        
        users = session.query(User).filter(User.id.in_(user_ids)).all()
        jobs = session.query(Job).filter(Job.id.in_(job_ids)).all()
        
        user_dict = {user.id: user for user in users}
        job_dict = {job.id: job for job in jobs}
        
        for user_id in user_ids:
            user = user_dict.get(user_id)
            if not user:
                continue
                
            for job_id in job_ids:
                job = job_dict.get(job_id)
                if not job:
                    continue
                
                match_score = self.calculate_job_match_score(user, job)
                results.append(match_score)
        
        return results
    
    def update_matching_weights(self, skills_weight: float = None, 
                               experience_weight: float = None,
                               location_weight: float = None,
                               description_weight: float = None):
        """Update the weights used for matching calculation"""
        if skills_weight is not None:
            self.skills_weight = skills_weight
        if experience_weight is not None:
            self.experience_weight = experience_weight
        if location_weight is not None:
            self.location_weight = location_weight
        if description_weight is not None:
            self.description_weight = description_weight
        
        # Normalize weights to sum to 1
        total = self.skills_weight + self.experience_weight + self.location_weight + self.description_weight
        self.skills_weight /= total
        self.experience_weight /= total
        self.location_weight /= total
        self.description_weight /= total