import spacy
from typing import List, Dict, Optional
import PyPDF2
import docx
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import openai
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class ResumeService:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Please install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
        
        self.skills_database = [
            "python", "javascript", "java", "c++", "react", "angular", "vue",
            "node.js", "express", "django", "flask", "spring", "sql", "mysql",
            "postgresql", "mongodb", "redis", "aws", "azure", "docker", "kubernetes",
            "git", "jenkins", "terraform", "machine learning", "data science",
            "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn"
        ]
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            return ""
    
    def extract_text_from_resume(self, file_path: str) -> str:
        """Extract text from resume file"""
        if file_path.lower().endswith('.pdf'):
            return self.extract_text_from_pdf(file_path)
        elif file_path.lower().endswith('.docx'):
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError("Unsupported file format. Please use PDF or DOCX.")
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.skills_database:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        # Use NLP to find additional technical terms
        if self.nlp:
            doc = self.nlp(text)
            technical_terms = []
            
            for token in doc:
                if (token.pos_ in ['NOUN', 'PROPN'] and 
                    len(token.text) > 2 and 
                    not token.is_stop and 
                    token.text.isalpha()):
                    technical_terms.append(token.text.lower())
            
            # Add high-frequency technical terms
            from collections import Counter
            term_freq = Counter(technical_terms)
            for term, freq in term_freq.most_common(10):
                if freq > 1 and term not in found_skills:
                    found_skills.append(term)
        
        return list(set(found_skills))
    
    def extract_experience_years(self, text: str) -> Optional[int]:
        """Extract years of experience from resume"""
        patterns = [
            r'(\d+)\s*years?\s*(?:of\s*)?experience',
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:professional\s*)?experience',
            r'experience\s*(?:of\s*)?(\d+)\s*years?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))
        
        return None
    
    def calculate_ats_score(self, text: str) -> float:
        """Calculate ATS (Applicant Tracking System) friendliness score"""
        score = 100.0
        
        # Check for common ATS issues
        issues = []
        
        # Check for tables, images, graphics (basic heuristics)
        if len(re.findall(r'\t+', text)) > 5:
            score -= 10
            issues.append("Contains tables or unusual formatting")
        
        # Check for contact information
        if not re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
            score -= 15
            issues.append("Missing email address")
        
        if not re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text):
            score -= 10
            issues.append("Missing phone number")
        
        # Check for standard sections
        sections = ['experience', 'education', 'skills']
        for section in sections:
            if section.lower() not in text.lower():
                score -= 5
                issues.append(f"Missing {section} section")
        
        # Check for excessive special characters
        special_chars = len(re.findall(r'[^\w\s\-.,()@]', text))
        if special_chars > 20:
            score -= 5
            issues.append("Too many special characters")
        
        return max(score, 0.0)
    
    def analyze_resume(self, file_path: str) -> Dict:
        """Comprehensive resume analysis"""
        try:
            text = self.extract_text_from_resume(file_path)
            
            if not text.strip():
                raise ValueError("Could not extract text from resume file")
            
            skills = self.extract_skills(text)
            experience_years = self.extract_experience_years(text)
            ats_score = self.calculate_ats_score(text)
            
            # Calculate overall resume score
            overall_score = 70.0  # Base score
            
            if len(skills) > 5:
                overall_score += 10
            if len(skills) > 10:
                overall_score += 10
            
            if experience_years:
                if experience_years > 2:
                    overall_score += 10
                if experience_years > 5:
                    overall_score += 10
            
            # Adjust for ATS score
            overall_score = (overall_score + ats_score) / 2
            
            strengths = []
            improvements = []
            
            if len(skills) > 8:
                strengths.append("Strong technical skill set")
            else:
                improvements.append("Consider adding more relevant technical skills")
            
            if experience_years and experience_years > 3:
                strengths.append("Solid professional experience")
            elif not experience_years:
                improvements.append("Clearly state years of experience")
            
            if ats_score > 80:
                strengths.append("ATS-friendly format")
            else:
                improvements.append("Improve ATS compatibility")
            
            if len(text.split()) > 300:
                strengths.append("Comprehensive content")
            else:
                improvements.append("Add more detailed descriptions")
            
            return {
                'score': round(overall_score, 1),
                'strengths': strengths,
                'improvements': improvements,
                'ats_score': round(ats_score, 1),
                'extracted_skills': skills,
                'experience_years': experience_years
            }
            
        except Exception as e:
            logger.error(f"Error analyzing resume: {str(e)}")
            raise ValueError(f"Resume analysis failed: {str(e)}")
    
    def optimize_for_job(self, file_path: str, job_description: str) -> Dict:
        """Optimize resume for specific job posting"""
        try:
            resume_text = self.extract_text_from_resume(file_path)
            
            if not settings.OPENAI_API_KEY:
                return self._basic_optimization(resume_text, job_description)
            
            # Use OpenAI for advanced optimization
            prompt = f"""
            Analyze this resume and job description to provide optimization suggestions:

            RESUME:
            {resume_text[:2000]}  # Limit text length

            JOB DESCRIPTION:
            {job_description[:1000]}

            Please provide:
            1. Specific suggestions to better match this job
            2. Keywords that should be added
            3. Sections that need improvement
            4. ATS optimization recommendations

            Format your response as structured recommendations.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            ai_suggestions = response.choices[0].message.content
            
            # Extract keywords from job description
            job_keywords = self._extract_job_keywords(job_description)
            resume_keywords = self.extract_skills(resume_text)
            
            missing_keywords = [kw for kw in job_keywords if kw not in resume_keywords]
            
            return {
                'optimized_content': ai_suggestions,
                'suggestions': ai_suggestions.split('\n')[:5],  # First 5 suggestions
                'keyword_improvements': missing_keywords[:10]  # Top 10 missing keywords
            }
            
        except Exception as e:
            logger.error(f"Error optimizing resume: {str(e)}")
            return self._basic_optimization(resume_text, job_description)
    
    def _basic_optimization(self, resume_text: str, job_description: str) -> Dict:
        """Basic optimization without OpenAI"""
        job_keywords = self._extract_job_keywords(job_description)
        resume_keywords = self.extract_skills(resume_text)
        
        missing_keywords = [kw for kw in job_keywords if kw not in resume_keywords]
        
        suggestions = [
            "Tailor your resume summary to match job requirements",
            "Add relevant keywords from the job description",
            "Quantify your achievements with specific numbers",
            "Highlight relevant experience for this role",
            "Ensure your skills section matches job requirements"
        ]
        
        return {
            'optimized_content': "Basic optimization completed. Consider using OpenAI API for advanced suggestions.",
            'suggestions': suggestions,
            'keyword_improvements': missing_keywords[:10]
        }
    
    def _extract_job_keywords(self, job_description: str) -> List[str]:
        """Extract important keywords from job description"""
        job_text = job_description.lower()
        
        # Find skills mentioned in job description
        found_keywords = []
        for skill in self.skills_database:
            if skill.lower() in job_text:
                found_keywords.append(skill)
        
        # Use TF-IDF for additional keyword extraction
        if self.nlp:
            doc = self.nlp(job_description)
            important_terms = []
            
            for token in doc:
                if (token.pos_ in ['NOUN', 'PROPN'] and 
                    len(token.text) > 2 and 
                    not token.is_stop and 
                    token.text.isalpha()):
                    important_terms.append(token.text.lower())
            
            # Get most frequent terms
            from collections import Counter
            term_freq = Counter(important_terms)
            for term, freq in term_freq.most_common(15):
                if term not in found_keywords:
                    found_keywords.append(term)
        
        return found_keywords[:20]  # Return top 20 keywords