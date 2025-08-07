#app/resume_matcher.py
"""
Resume-JD Matching System with Ollama Integration
Description: Advanced resume analysis and job matching system using Ollama with Gemma3:1b
"""

import os
import json
import re
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib

# Core libraries
import PyPDF2
import fitz  
import ollama
import pandas as pd
from dataclasses import dataclass, asdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Download required NLTK data
try:
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
except:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('resume_matcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class JobDescription:
    """Job Description data structure"""
    title: str
    company: str
    description: str
    required_skills: List[str]
    preferred_skills: List[str]
    experience_level: str
    location: str
    salary_range: Optional[str] = None

@dataclass
class ResumeData:
    """Resume data structure"""
    name: str
    email: str
    phone: str
    skills: List[str]
    experience: List[Dict]
    education: List[Dict]
    certifications: List[str]
    projects: List[Dict]
    summary: str
    total_experience_years: float

@dataclass
class MatchResult:
    """Match result data structure"""
    overall_score: float
    skills_match: float
    experience_match: float
    education_match: float
    detailed_analysis: Dict
    recommendations: List[str]
    missing_skills: List[str]
    matching_skills: List[str]
    timestamp: str

class PDFExtractor:
    """Enhanced PDF content extraction"""
    
    @staticmethod
    def extract_with_pymupdf(pdf_path: str) -> str:
        """Extract text using PyMuPDF (better for complex layouts)"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            return ""
    
    @staticmethod
    def extract_with_pypdf2(pdf_path: str) -> str:
        """Extract text using PyPDF2 (fallback)"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            return ""
    
    @classmethod
    def extract_text(cls, pdf_path: str) -> str:
        """Extract text with fallback methods"""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Try PyMuPDF first (better accuracy)
        text = cls.extract_with_pymupdf(pdf_path)
        
        # Fallback to PyPDF2 if needed
        if not text.strip():
            text = cls.extract_with_pypdf2(pdf_path)
        
        if not text.strip():
            raise ValueError("Could not extract text from PDF")
        
        return text.strip()

class TextProcessor:
    """Advanced text processing utilities"""
    
    def __init__(self):
        try:
            self.stop_words = set(stopwords.words('english'))
            self.lemmatizer = WordNetLemmatizer()
        except:
            self.stop_words = set()
            self.lemmatizer = None
            logger.warning("NLTK resources not available, using basic processing")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s@.-]', ' ', text)
        return text.strip()
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from text"""
        skill_patterns = [
            r'\b(?:Python|Java|JavaScript|C\+\+|C#|Ruby|Go|Rust|Swift|Kotlin)\b',
            r'\b(?:React|Angular|Vue|Node\.js|Django|Flask|Spring|Laravel)\b',
            r'\b(?:AWS|Azure|GCP|Docker|Kubernetes|Jenkins|Git|CI/CD)\b',
            r'\b(?:MySQL|PostgreSQL|MongoDB|Redis|Elasticsearch|Cassandra)\b',
            r'\b(?:Machine Learning|Deep Learning|AI|TensorFlow|PyTorch|Scikit-learn)\b',
            r'\b(?:Data Science|Analytics|Statistics|R|Pandas|NumPy|Matplotlib)\b',
            r'\b(?:Agile|Scrum|DevOps|Microservices|REST|API|GraphQL)\b'
        ]
        
        skills = set()
        text_upper = text.upper()
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            skills.update(matches)
        
        # Additional common skills
        common_skills = [
            'HTML', 'CSS', 'SQL', 'NoSQL', 'Linux', 'Windows', 'MacOS',
            'Tableau', 'Power BI', 'Excel', 'JIRA', 'Confluence'
        ]
        
        for skill in common_skills:
            if skill.upper() in text_upper:
                skills.add(skill)
        
        return list(skills)
    
    def extract_email(self, text: str) -> str:
        """Extract email address"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else ""
    
    def extract_phone(self, text: str) -> str:
        """Extract phone number"""
        phone_patterns = [
            r'\+?\d{1,4}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            r'\(\d{3}\)\s*\d{3}-\d{4}',
            r'\d{3}-\d{3}-\d{4}'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return ""
    
    def calculate_experience_years(self, text: str) -> float:
        """Calculate total years of experience"""
        experience_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',
            r'(?:experience|exp).*?(\d+(?:\.\d+)?)\s*(?:years?|yrs?)',
            r'(\d+)\+?\s*(?:years?|yrs?)'
        ]
        
        years = []
        for pattern in experience_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                try:
                    years.append(float(match))
                except:
                    continue
        
        return max(years) if years else 0.0

class OllamaClient:
    """Enhanced Ollama client with error handling and optimization"""

    def __init__(self, model: str = "gemma3:1b"):
        self.model = model
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        # Create Ollama client with custom host
        self.client = ollama
        self.verify_model()

    def verify_model(self):
        try:
            model_list = self.client.list()

            # Handle response from new Ollama Python client
            if hasattr(model_list, "models"):
                models = model_list.models
            else:
                models = model_list

            for model in models:
                model_name = getattr(model, "model", None)
                if model_name == self.model:
                    return True

            return False  # model not found

        except Exception as e:
            print(f"Error verifying model: {e}")
            return False

    def generate_analysis(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate analysis using Ollama"""
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'num_predict': max_tokens,
                    'temperature': 0.3,
                    'top_p': 0.9,
                    'repeat_penalty': 1.1
                }
            )
            return response['response'].strip()
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return f"Analysis unavailable: {str(e)}"

    def analyze_resume_match(self, resume_text: str, jd_text: str) -> dict:
        """Comprehensive resume-JD analysis"""
        prompt = f"""
        Analyze the following resume against the job description and provide a detailed assessment:

        JOB DESCRIPTION:
        {jd_text[:1000]}...

        RESUME:
        {resume_text[:1500]}...

        Please provide analysis in the following format:
        SKILLS_MATCH: [0-100 score]
        EXPERIENCE_MATCH: [0-100 score]
        EDUCATION_MATCH: [0-100 score]
        OVERALL_FIT: [0-100 score]

        STRENGTHS:
        - [List key strengths]

        GAPS:
        - [List skill/experience gaps]

        RECOMMENDATIONS:
        - [Specific recommendations for improvement]

        Keep the analysis concise but comprehensive.
        """

        analysis = self.generate_analysis(prompt, max_tokens=600)
        return self._parse_analysis(analysis)

    def _parse_analysis(self, analysis: str) -> dict:
        """Parse Ollama analysis response"""
        result = {
            'skills_match': 0,
            'experience_match': 0,
            'education_match': 0,
            'overall_fit': 0,
            'strengths': [],
            'gaps': [],
            'recommendations': []
        }

        try:
            # Extract numerical scores
            score_patterns = {
                'skills_match': r'SKILLS_MATCH:\s*(\d+)',
                'experience_match': r'EXPERIENCE_MATCH:\s*(\d+)',
                'education_match': r'EDUCATION_MATCH:\s*(\d+)',
                'overall_fit': r'OVERALL_FIT:\s*(\d+)'
            }

            for key, pattern in score_patterns.items():
                match = re.search(pattern, analysis, re.IGNORECASE)
                if match:
                    result[key] = min(100, max(0, int(match.group(1))))

            # Extract lists
            sections = {
                'strengths': r'STRENGTHS:(.*?)(?=GAPS:|RECOMMENDATIONS:|$)',
                'gaps': r'GAPS:(.*?)(?=RECOMMENDATIONS:|$)',
                'recommendations': r'RECOMMENDATIONS:(.*?)$'
            }

            for key, pattern in sections.items():
                match = re.search(pattern, analysis, re.IGNORECASE | re.DOTALL)
                if match:
                    items = re.findall(r'-\s*(.+)', match.group(1))
                    result[key] = [item.strip() for item in items if item.strip()]

        except Exception as e:
            logger.error(f"Error parsing analysis: {e}")

        return result

class ResumeParser:
    """Advanced resume parsing with AI assistance"""
    
    def __init__(self, text_processor: TextProcessor, ollama_client: OllamaClient):
        self.text_processor = text_processor
        self.ollama_client = ollama_client
    
    def parse_resume(self, text: str) -> ResumeData:
        """Parse resume text into structured data"""
        # Basic extraction
        name = self._extract_name(text)
        email = self.text_processor.extract_email(text)
        phone = self.text_processor.extract_phone(text)
        skills = self.text_processor.extract_skills(text)
        experience_years = self.text_processor.calculate_experience_years(text)
        
        # AI-assisted extraction
        ai_analysis = self._ai_parse_resume(text)
        
        return ResumeData(
            name=name,
            email=email,
            phone=phone,
            skills=skills + ai_analysis.get('additional_skills', []),
            experience=ai_analysis.get('experience', []),
            education=ai_analysis.get('education', []),
            certifications=ai_analysis.get('certifications', []),
            projects=ai_analysis.get('projects', []),
            summary=ai_analysis.get('summary', ''),
            total_experience_years=experience_years
        )
    
    def _extract_name(self, text: str) -> str:
        """Extract candidate name"""
        lines = text.split('\n')[:5]  # Check first 5 lines
        for line in lines:
            line = line.strip()
            if len(line) > 3 and len(line) < 50:
                # Simple heuristic for name detection
                words = line.split()
                if 2 <= len(words) <= 4 and all(word.isalpha() for word in words):
                    return line
        return "Unknown Candidate"
    
    def _ai_parse_resume(self, text: str) -> Dict:
        """Use AI to extract structured resume data"""
        prompt = f"""
        Parse the following resume and extract structured information:

        RESUME:
        {text[:2000]}...

        Extract and format as follows:
        SUMMARY: [Brief professional summary]
        EXPERIENCE: [Job titles, companies, years - one per line]
        EDUCATION: [Degrees, institutions - one per line]
        CERTIFICATIONS: [List certifications - one per line]
        PROJECTS: [Project names and brief descriptions - one per line]
        ADDITIONAL_SKILLS: [Any technical skills not already obvious]

        Keep responses concise and accurate.
        """
        
        analysis = self.ollama_client.generate_analysis(prompt, max_tokens=400)
        return self._parse_resume_analysis(analysis)
    
    def _parse_resume_analysis(self, analysis: str) -> Dict:
        """Parse AI resume analysis"""
        result = {
            'summary': '',
            'experience': [],
            'education': [],
            'certifications': [],
            'projects': [],
            'additional_skills': []
        }
        
        try:
            sections = {
                'summary': r'SUMMARY:\s*(.+?)(?=EXPERIENCE:|EDUCATION:|$)',
                'experience': r'EXPERIENCE:(.*?)(?=EDUCATION:|CERTIFICATIONS:|$)',
                'education': r'EDUCATION:(.*?)(?=CERTIFICATIONS:|PROJECTS:|$)',
                'certifications': r'CERTIFICATIONS:(.*?)(?=PROJECTS:|ADDITIONAL_SKILLS:|$)',
                'projects': r'PROJECTS:(.*?)(?=ADDITIONAL_SKILLS:|$)',
                'additional_skills': r'ADDITIONAL_SKILLS:(.*?)$'
            }
            
            for key, pattern in sections.items():
                match = re.search(pattern, analysis, re.IGNORECASE | re.DOTALL)
                if match:
                    content = match.group(1).strip()
                    if key == 'summary':
                        result[key] = content
                    else:
                        items = [item.strip() for item in content.split('\n') if item.strip()]
                        result[key] = items
        
        except Exception as e:
            logger.error(f"Error parsing resume analysis: {e}")
        
        return result

class MatchingEngine:
    """Advanced matching engine with multiple algorithms"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
    
    def calculate_match_score(self, resume_data: ResumeData, job_desc: JobDescription) -> MatchResult:
        """Calculate comprehensive match score"""
        
        # 1. Skills matching
        skills_score = self._calculate_skills_match(resume_data.skills, 
                                                   job_desc.required_skills + job_desc.preferred_skills)
        
        # 2. Experience matching
        experience_score = self._calculate_experience_match(resume_data, job_desc)
        
        # 3. Text similarity
        text_score = self._calculate_text_similarity(resume_data, job_desc)
        
        # 4. AI analysis
        ai_analysis = self.ollama_client.analyze_resume_match(
            self._resume_to_text(resume_data),
            self._jd_to_text(job_desc)
        )
        
        # Weighted final score
        weights = {
            'skills': 0.35,
            'experience': 0.25,
            'text_similarity': 0.20,
            'ai_analysis': 0.20
        }
        
        overall_score = (
            skills_score * weights['skills'] +
            experience_score * weights['experience'] +
            text_score * weights['text_similarity'] +
            ai_analysis.get('overall_fit', 0) * weights['ai_analysis']
        )
        
        # Identify matching and missing skills
        matching_skills, missing_skills = self._analyze_skills_gap(
            resume_data.skills, job_desc.required_skills
        )
        
        return MatchResult(
            overall_score=round(overall_score, 2),
            skills_match=round(skills_score, 2),
            experience_match=round(experience_score, 2),
            education_match=75.0,  # Placeholder
            detailed_analysis=ai_analysis,
            recommendations=ai_analysis.get('recommendations', []),
            missing_skills=missing_skills,
            matching_skills=matching_skills,
            timestamp=datetime.now().isoformat()
        )
    
    def _calculate_skills_match(self, resume_skills: List[str], job_skills: List[str]) -> float:
        """Calculate skills matching percentage"""
        if not job_skills:
            return 100.0

        try:
            resume_skills_lower = [str(skill).lower() for skill in resume_skills]
            job_skills_lower = [str(skill).lower() for skill in job_skills]
        except Exception as e:
            logger.error(f"Skill lowercasing error: {e}")
            return 0.0

        matches = sum(1 for skill in job_skills_lower if skill in resume_skills_lower)
        return (matches / len(job_skills_lower)) * 100

    def _calculate_experience_match(self, resume_data: ResumeData, job_desc: JobDescription) -> float:
        """Calculate experience level match"""
        experience_levels = {
            'entry': (0, 2),
            'junior': (1, 3),
            'mid': (3, 6),
            'senior': (6, 10),
            'lead': (8, 15),
            'principal': (10, 20)
        }

        try:
            experience_key = str(job_desc.experience_level).lower()
            required_range = experience_levels.get(experience_key, (0, 100))
        except Exception as e:
            logger.error(f"Experience level error: {e}")
            required_range = (0, 100)

        candidate_years = resume_data.total_experience_years

        if required_range[0] <= candidate_years <= required_range[1]:
            return 100.0
        elif candidate_years < required_range[0]:
            gap = required_range[0] - candidate_years
            return max(0, 100 - (gap * 20))
        else:  # Over-qualified
            excess = candidate_years - required_range[1]
            return max(70, 100 - (excess * 5))
    
    def _calculate_text_similarity(self, resume_data: ResumeData, job_desc: JobDescription) -> float:
        """Calculate text similarity using TF-IDF"""
        try:
            resume_text = self._resume_to_text(resume_data)
            jd_text = self._jd_to_text(job_desc)
            
            tfidf_matrix = self.vectorizer.fit_transform([resume_text, jd_text])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return similarity * 100
        except Exception as e:
            logger.error(f"Text similarity calculation error: {e}")
            return 50.0

    def _analyze_skills_gap(self, resume_skills: List[str], required_skills: List[str]) -> Tuple[List[str], List[str]]:
        """Analyze skills gap"""
        try:
            resume_skills_lower = [str(skill).lower() for skill in resume_skills]
            required_skills_lower = [str(skill).lower() for skill in required_skills]
        except Exception as e:
            logger.error(f"Skill gap analysis error: {e}")
            return [], required_skills

        matching = [skill for skill in required_skills_lower if skill in resume_skills_lower]
        missing = [skill for skill in required_skills_lower if skill not in resume_skills_lower]

        return matching, missing

    
    def _resume_to_text(self, resume_data: ResumeData) -> str:
        """Convert resume data to text"""
        return f"{resume_data.summary} {' '.join(resume_data.skills)}"
    
    def _jd_to_text(self, job_desc: JobDescription) -> str:
        """Convert job description to text"""
        return f"{job_desc.description} {' '.join(job_desc.required_skills + job_desc.preferred_skills)}"

class ResumeJDMatcher:
    """Main application class"""
    
    def __init__(self, model: str = "gemma3:1b"):
        self.text_processor = TextProcessor()
        self.ollama_client = OllamaClient(model)
        self.resume_parser = ResumeParser(self.text_processor, self.ollama_client)
        self.matching_engine = MatchingEngine(self.ollama_client)
        self.pdf_extractor = PDFExtractor()
        
        # Create results directory
        self.results_dir = Path("matching_results")
        self.results_dir.mkdir(exist_ok=True)
        
        logger.info("Resume-JD Matcher initialized successfully")
    
    def process_resume(self, pdf_path: str) -> ResumeData:
        """Process resume PDF and extract data"""
        logger.info(f"Processing resume: {pdf_path}")
        
        # Extract text from PDF
        text = self.pdf_extractor.extract_text(pdf_path)
        
        # Parse resume data
        resume_data = self.resume_parser.parse_resume(text)
        
        logger.info(f"Resume processed: {resume_data.name}")
        return resume_data
    
    def match_resume_to_job(self, pdf_path: str, job_desc: Optional[JobDescription] = None) -> MatchResult:
        """Match resume to job description"""
        if job_desc is None:
            logger.info("No job description provided, using sample JD")
        
        # Process resume
        resume_data = self.process_resume(pdf_path)
        
        # Calculate match
        match_result = self.matching_engine.calculate_match_score(resume_data, job_desc)
        
        # Save results
        self._save_results(resume_data, job_desc, match_result)
        
        return match_result
    
    def _save_results(self, resume_data: ResumeData, job_desc: JobDescription, match_result: MatchResult):
        """Save matching results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"match_result_{timestamp}.json"
        
        results = {
            'resume': asdict(resume_data),
            'job_description': asdict(job_desc),
            'match_result': asdict(match_result)
        }
        
        with open(self.results_dir / filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved: {filename}")
    
    def generate_report(self, match_result: MatchResult, resume_data: ResumeData, job_desc: JobDescription) -> str:
        """Generate detailed matching report"""
        report = f"""
        ═══════════════════════════════════════════════════════════════
                        RESUME-JD MATCHING REPORT
        ═══════════════════════════════════════════════════════════════
        
        CANDIDATE: {resume_data.name}
        JOB TITLE: {job_desc.title}
        COMPANY: {job_desc.company}
        ANALYSIS DATE: {match_result.timestamp}
        
        ═══════════════════════════════════════════════════════════════
                            MATCH SCORES
        ═══════════════════════════════════════════════════════════════
        
        🎯 OVERALL MATCH:        {match_result.overall_score}%
        🛠️  SKILLS MATCH:        {match_result.skills_match}%
        💼 EXPERIENCE MATCH:     {match_result.experience_match}%
        🎓 EDUCATION MATCH:      {match_result.education_match}%
        
        ═══════════════════════════════════════════════════════════════
                            SKILLS ANALYSIS
        ═══════════════════════════════════════════════════════════════
        
        ✅ MATCHING SKILLS ({len(match_result.matching_skills)}):
        {chr(10).join([f"   • {skill}" for skill in match_result.matching_skills])}
        
        ❌ MISSING SKILLS ({len(match_result.missing_skills)}):
        {chr(10).join([f"   • {skill}" for skill in match_result.missing_skills])}
        
        ═══════════════════════════════════════════════════════════════
                            RECOMMENDATIONS
        ═══════════════════════════════════════════════════════════════
        
        {chr(10).join([f"   • {rec}" for rec in match_result.recommendations])}
        
        ═══════════════════════════════════════════════════════════════
                            CANDIDATE SUMMARY
        ═══════════════════════════════════════════════════════════════
        
        Experience: {resume_data.total_experience_years} years
        Email: {resume_data.email}
        Phone: {resume_data.phone}
        
        Total Skills: {len(resume_data.skills)}
        Certifications: {len(resume_data.certifications)}
        
        ═══════════════════════════════════════════════════════════════
        """
        logger.info(f"Generated report for: {resume_data.name}")
        return report
