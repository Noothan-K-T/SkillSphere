# /api/index.py

import os
import logging
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr, model_validator, ValidationError
from httpx import AsyncClient, HTTPStatusError
from typing import List, Dict, Optional
from beanie import Document, init_beanie, PydanticObjectId
import motor.motor_asyncio
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer

# --- Logging & Environment ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
dotenv_path = ROOT_DIR / '.env'
load_dotenv(dotenv_path)

# --- Environment Variables & Constants ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-secret-key").strip()
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

if GOOGLE_API_KEY:
    logger.info("Google API key loaded from .env; Gemini calls are enabled.")
else:
    logger.warning("No GOOGLE_API_KEY found in environment; falling back to local parsing logic.")

# --- FastAPI App ---
app = FastAPI(
    title="SkillSphere API",
    description="API for parsing resumes and generating career roadmaps.",
    version="1.0.0",
    docs_url="/docs" if os.getenv("VERCEL_ENV") != "production" else None,
    redoc_url="/redoc" if os.getenv("VERCEL_ENV") != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Client ---
if not MONGO_CONNECTION_STRING:
    logger.error("FATAL: MONGO_CONNECTION_STRING is not set.")
    raise ValueError("MONGO_CONNECTION_STRING environment variable not set.")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_CONNECTION_STRING)

# --- Models ---
class Experience(BaseModel):
    role: str
    company: Optional[str] = "Organization"
    dates: Optional[str] = "Not Specified"
    summary: Optional[str] = None
    
    @model_validator(mode='before')
    @classmethod
    def handle_ai_variations(cls, data):
        if isinstance(data, dict):
            if 'title' in data and 'role' not in data: data['role'] = data['title']
            if 'description' in data and 'summary' not in data: data['summary'] = data['description']
            if 'project' in data.get('role', '').lower() and 'company' not in data: data['company'] = 'Personal Project'
        return data

class Education(BaseModel):
    degree: str
    university: str
    dates: Optional[str] = None
    graduation_year: Optional[int] = None
    
    @model_validator(mode="before")
    @classmethod
    def handle_ai_variations(cls, data):
        if isinstance(data, dict):
            if "university" not in data:
                if "institution" in data: data["university"] = data["institution"]
                elif "location" in data: data["university"] = data["location"]
        return data

class ParsedResume(BaseModel):
    skills: Dict[str, List[str]]
    experience: List[Experience]
    education: List[Education]

class RoadmapStep(BaseModel):
    step: int
    title: str = "Learning Step"
    description: str = ""
    resources: List[str] = Field(default_factory=list)

class RoadmapRequest(BaseModel):
    current_role: str = Field(..., example="Junior Python Developer")
    desired_role: str = Field(..., example="Senior Machine Learning Engineer")
    current_skills: List[str] = Field(default=[], example=["Python", "FastAPI", "SQL"])

class SkillGap(BaseModel):
    matching_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)

class RoadmapResponse(BaseModel):
    skill_gap: Optional[SkillGap] = None
    roadmap: List[RoadmapStep]

class SaveRoadmapPayload(BaseModel):
    roadmap_data: RoadmapRequest
    roadmap_response: RoadmapResponse

class SavedRoadmap(Document):
    user_email: str = Field(..., index=True)
    current_role: str = "Unknown Role"
    desired_role: str = "Desired Role"
    skill_gap: Optional[SkillGap] = None
    roadmap: List[RoadmapStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    class Settings:
        name = "roadmaps"

class UserAccount(Document):
    email: EmailStr = Field(..., unique=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    class Settings:
        name = "users"

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    id: PydanticObjectId
    email: EmailStr
    class Config:
        arbitrary_types_allowed = True

class ResumeParseRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)

# --- Database Init ---
async def init_db():
    """Initialize Beanie ODM on application startup."""
    try:
        await init_beanie(
            database=client.skillsphere_db,
            document_models=[UserAccount, SavedRoadmap]
        )
    except Exception as e:
        logger.error(f"Error initializing Beanie: {e}")
        raise RuntimeError("Database connection failed.")

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception during request processing")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# --- Auth Setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password: str) -> str: return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool: return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not JWT_SECRET_KEY: 
        raise HTTPException(status_code=500, detail="JWT Secret Key not configured")
    
    try:
        # Added 60s leeway for clock skew
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"leeway": 60})
        email: str = payload.get("sub")
        if email is None: 
            credentials_exception.detail = "Token validation failed: Missing email claim."
            raise credentials_exception
    except JWTError as e:
        credentials_exception.detail = f"Token validation failed: {str(e)}"
        raise credentials_exception
    
    user = await UserAccount.find_one(UserAccount.email == email)
    if user is None: 
        credentials_exception.detail = f"Account for {email} not found."
        raise credentials_exception
        
    return User(id=user.id, email=user.email)

# --- Helper Functions ---
def clean_json_response(text: str) -> str:
    """Extracts JSON structure from text robustly."""
    text = text.strip()
    start_brace = text.find('{')
    start_bracket = text.find('[')
    
    start_idx = -1
    if start_brace != -1 and start_bracket != -1:
        start_idx = min(start_brace, start_bracket)
    elif start_brace != -1:
        start_idx = start_brace
    elif start_bracket != -1:
        start_idx = start_bracket
        
    end_brace = text.rfind('}')
    end_bracket = text.rfind(']')
    
    end_idx = -1
    if end_brace != -1 and end_bracket != -1:
        end_idx = max(end_brace, end_bracket)
    elif end_brace != -1:
        end_idx = end_brace
    elif end_bracket != -1:
        end_idx = end_bracket
        
    if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
        return text[start_idx:end_idx+1]
        
    return text

def fallback_parse_resume(resume_text: str) -> str:
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    text_lower = resume_text.lower()

    known_skills = [
        # Languages
        'python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'golang', 'rust', 'swift', 'kotlin', 'ruby', 'php', 'sql', 'html', 'css',
        # Frameworks & Libraries
        'react', 'next.js', 'vue', 'angular', 'fastapi', 'flask', 'django', 'spring boot', 'express', 'node.js', 'react native', 'flutter',
        'tailwind', 'bootstrap', 'material ui', 'redux', 'pytorch', 'tensorflow', 'scikit-learn', 'pandas', 'numpy', 'opencv',
        # Tools & Platforms
        'aws', 'azure', 'google cloud', 'gcp', 'docker', 'kubernetes', 'git', 'github', 'jenkins', 'terraform', 'ansible', 'linux',
        'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch', 'graphql', 'rest api', 'firebase', 'postman',
        # Concepts & Methodology
        'machine learning', 'artificial intelligence', 'data science', 'devops', 'agile', 'scrum', 'backend', 'frontend', 'fullstack',
        'microservices', 'cicd', 'unit testing', 'system design', 'cloud computing', 'cybersecurity'
    ]

    detected_skills = sorted({skill.title() for skill in known_skills if re.search(rf'\b{re.escape(skill)}\b', text_lower)})
    if not detected_skills:
        # Fallback to general word extraction if no known skills found
        words = re.findall(r"\b[a-zA-Z+#]{2,}\b", text_lower)
        detected_skills = sorted({word.title() for word in words if len(word) > 2 and word not in ['the', 'and', 'for', 'with']})[:20]

    def categorize_skills(skills):
        categories = {
            "Languages": ['python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'golang', 'rust', 'swift', 'kotlin', 'ruby', 'php', 'sql', 'html', 'css'],
            "Frameworks": ['react', 'next.js', 'vue', 'angular', 'fastapi', 'flask', 'django', 'spring boot', 'express', 'node.js', 'react native', 'flutter', 'tailwind', 'bootstrap', 'material ui', 'redux', 'pytorch', 'tensorflow', 'scikit-learn', 'pandas', 'numpy', 'opencv'],
            "Tools & Cloud": ['aws', 'azure', 'google cloud', 'gcp', 'docker', 'kubernetes', 'git', 'github', 'jenkins', 'terraform', 'ansible', 'linux', 'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch', 'graphql', 'rest api', 'firebase', 'postman'],
            "Concepts": ['machine learning', 'artificial intelligence', 'data science', 'devops', 'agile', 'scrum', 'backend', 'frontend', 'fullstack', 'microservices', 'cicd', 'unit testing', 'system design', 'cloud computing', 'cybersecurity']
        }
        
        result = {}
        processed = set()
        for cat, keywords in categories.items():
            found = [s for s in skills if s.lower() in keywords]
            if found:
                result[cat] = found
                for s in found: processed.add(s)
        
        remaining = [s for s in skills if s not in processed]
        if remaining:
            result["Other Skills"] = remaining
        return result

    skill_categories = categorize_skills(detected_skills)

    def extract_sections():
        sections = {'experience': [], 'education': [], 'skills': [], 'summary': [], 'other': []}
        current = 'other'
        for line in lines:
            lower = line.lower()
            if any(keyword in lower for keyword in ['experience', 'work experience', 'professional experience', 'employment history', 'career history']):
                current = 'experience'
                continue
            if any(keyword in lower for keyword in ['education', 'academic background', 'qualifications', 'degree']):
                current = 'education'
                continue
            if any(keyword in lower for keyword in ['skills', 'technical skills', 'expertise']):
                current = 'skills'
                continue
            if any(keyword in lower for keyword in ['summary', 'profile', 'about']):
                current = 'summary'
                continue
            sections[current].append(line)
        return sections

    sections = extract_sections()

    def parse_experience():
        experience_items = []
        candidate_lines = sections['experience'] if sections['experience'] else lines[1:]
        
        date_pattern = r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|20\d{2}|19\d{2}|Present|Current|Now)\b'
        role_kws = [
            'engineer', 'developer', 'manager', 'lead', 'consultant', 'analyst', 'intern', 'scientist', 'specialist', 'architect', 'designer', 'executive', 'admin', 'principal', 'head',
            'teacher', 'instructor', 'professor', 'nurse', 'doctor', 'associate', 'assistant', 'clerk', 'technician', 'operator', 'student', 'fellow', 'trainee', 'representative', 'officer'
        ]
        comp_kws = ['inc', 'corp', 'llc', 'ltd', 'google', 'meta', 'spotify', 'amazon', 'netflix', 'microsoft', 'apple', 'university', 'college', 'foundation', 'institute', 'association']

        current_job = {'role': None, 'company': None, 'dates': None, 'summary': []}
        buffer = [] # Lines before a date that might be Role/Company

        for line in candidate_lines:
            line_clean = line.strip()
            if not line_clean: continue
            
            has_date = re.search(date_pattern, line_clean, re.I)
            # A role title should be short and contain a keyword
            is_role_kw = any(kw in line_clean.lower() for kw in role_kws)
            is_sentence = len(line_clean.split()) > 6 or any(line_clean.lower().startswith(v) for v in ['lead ', 'develop', 'manage', 'work', 'respon', 'create', 'build'])
            is_role = is_role_kw and not is_sentence
            
            if has_date:
                if current_job['dates']:
                    experience_items.append(current_job)
                    current_job = {'role': None, 'company': None, 'dates': None, 'summary': []}
                
                current_job['dates'] = line_clean
                for b_line in reversed(buffer):
                    b_is_role = any(kw in b_line.lower() for kw in role_kws) and len(b_line.split()) <= 6
                    b_is_comp = any(kw in b_line.lower() for kw in comp_kws)
                    if b_is_role and not current_job['role']:
                        current_job['role'] = b_line
                    elif (b_is_comp or b_line[0].isupper()) and not current_job['company']:
                        current_job['company'] = b_line
                
                # FINAL FALLBACK WITHIN BUFFER: If still no role but we have a company and another line
                if not current_job['role'] and buffer:
                    for b_line in buffer:
                        if b_line != current_job['company'] and len(b_line.split()) <= 6:
                            current_job['role'] = b_line
                            break
                buffer = []
            elif is_role and current_job['dates']:
                experience_items.append(current_job)
                current_job = {'role': line_clean, 'company': None, 'dates': None, 'summary': []}
                buffer = []
            elif current_job['dates']:
                current_job['summary'].append(line_clean)
            else:
                buffer.append(line_clean)

        if current_job['dates'] or current_job['role']:
            experience_items.append(current_job)

        parsed = []
        for job in experience_items[:5]:
            # ULTIMATE FALLBACK: If still no role but we have summary lines, take the first one
            role = job['role']
            if not role and job['summary']:
                role = job['summary'][0]
                job['summary'] = job['summary'][1:]
            
            role = role or "Professional Role"
            
            # Only strip names if it doesn't look like a role keywords
            has_role_kw = any(kw in role.lower() for kw in role_kws)
            if not has_role_kw:
                role = re.sub(r'^[A-Z][a-z]+\s+[A-Z][a-z]+[\.\-\:\|\s]*', '', role).strip()
            
            # Extract first clause (stop at punctuation)
            role = re.split(r'[\.\-\:\|]', role)[0].strip()
            
            parsed.append({
                'role': role[:80] or "Professional Role",
                'company': (job['company'] or "Organization")[:80],
                'dates': (job['dates'] or "Period TBD")[:50],
                'summary': " ".join(job['summary'])[:300] or "Experience background."
            })

        return parsed if parsed else [{
            'role': 'Professional',
            'company': 'Organization',
            'dates': 'Not specified',
            'summary': 'Details extracted from resume.'
        }]

    def parse_education():
        edu_lines = sections['education'] if sections['education'] else [line for line in lines if re.search(r'\b(bachelor|master|mba|phd|associate|degree|university|college|school)\b', line, re.I)]
        
        parsed_edu = []
        for line in edu_lines[:3]:
            if not line: continue
            year_match = re.search(r'\b(20\d{2}|19\d{2})\b', line)
            parts = [p.strip() for p in re.split(r',|\||@| at ', line) if p.strip()]
            parsed_edu.append({
                'degree': parts[0][:100] if parts else 'Degree',
                'university': parts[1][:100] if len(parts) > 1 else 'Institution',
                'dates': line.strip()[:50],
                'graduation_year': int(year_match.group(1)) if year_match else 2024
            })
        
        return parsed_edu if parsed_edu else [{'degree': 'Education', 'university': 'Institution', 'dates': 'Not specified', 'graduation_year': 2024}]

    return json.dumps({
        'skills': skill_categories,
        'experience': parse_experience(),
        'education': parse_education(),
    })


def fallback_generate_roadmap(current_role: str, desired_role: str, current_skills: List[str]) -> str:
    steps = [
        {
            'step': 1,
            'title': 'Master Foundations',
            'description': f'Deep dive into the core principles of {desired_role}. Since you already know {", ".join(current_skills[:3])}, focus on the architectural differences.',
            'resources': ['Roadmap.sh', 'FreeCodeCamp', 'Official Documentation']
        },
        {
            'step': 2,
            'title': 'Bridge Technical Gaps',
            'description': f'Identify and learn the top 3 tools required for {desired_role} that were missing from your profile.',
            'resources': ['Udemy Top Rated', 'Coursera Specializations', 'YouTube Crash Courses']
        },
        {
            'step': 3,
            'title': 'Practical Labs & Projects',
            'description': 'Build 2 mini-projects that demonstrate your new skills. This bridge the theoretical gap.',
            'resources': ['GitHub Topic Search', 'Frontend Mentor', 'Kaggle Datasets']
        },
        {
            'step': 4,
            'title': 'Advanced Industry Patterns',
            'description': f'Learn how {desired_role} professionals handle scalability, security, and performance in real-world environments.',
            'resources': ['System Design Primer', 'Medium Engineering Blogs', 'Tech Whitepapers']
        },
        {
            'step': 5,
            'title': 'Portfolio Refinement',
            'description': f'Update your resume and portfolio to reflect your transition from {current_role} to {desired_role}.',
            'resources': ['Canva Resume Builder', 'LinkedIn Optimization Tips']
        },
        {
            'step': 6,
            'title': 'Mock Interviews & Networking',
            'description': 'Conduct mock interviews and reach out to mentors in the field to finalize your transition.',
            'resources': ['Interviewing.io', 'ADPList Mentorship', 'LeetCode']
        }
    ]
    skill_gap = {'matching_skills': current_skills, 'missing_skills': ['Professional ' + desired_role + ' Standards', 'High-level Architecture']}
    return json.dumps({'skill_gap': skill_gap, 'roadmap': steps})


async def call_gemini_api(prompt: str, timeout: int = 90) -> str:
    if not GOOGLE_API_KEY:
        logger.info('Google API key is not configured, using local fallback.')
        if 'You are an expert resume parser.' in prompt:
            match = re.search(r"RESUME TEXT:\s*-+\s*(.+?)\s*-+", prompt, re.S)
            resume_text = match.group(1).strip() if match else prompt
            return fallback_parse_resume(resume_text)
        if 'You are an elite career coach.' in prompt:
            current_role = re.search(r'- Current Role:\s*(.+)', prompt)
            desired_role = re.search(r'- Desired Role:\s*(.+)', prompt)
            skills = re.search(r'- Current Skills:\s*(.+)', prompt)
            return fallback_generate_roadmap(
                current_role.group(1).strip() if current_role else 'Your current role',
                desired_role.group(1).strip() if desired_role else 'Your desired role',
                [s.strip() for s in skills.group(1).split(',')] if skills else []
            )
        raise HTTPException(status_code=500, detail='AI service is not configured.')
    
    clean_key = GOOGLE_API_KEY.strip()
    base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    api_url = f"{base_url}?key={clean_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json"
        }
    }
    
    try:
        async with AsyncClient() as client:
            resp = await client.post(api_url.strip(), json=payload, timeout=timeout)
            resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates") or []
        if not candidates:
            raise HTTPException(status_code=502, detail="AI returned an invalid response.")

        first = candidates[0]
        if "content" in first and "parts" in first["content"]:
            parts = first["content"]["parts"]
            if parts and "text" in parts[0]:
                return parts[0]["text"]
        
        raise HTTPException(status_code=502, detail="AI returned an unsupported response format.")
        
    except HTTPStatusError as e:
        logger.error(f"HTTP status error calling Gemini API: {e.response.status_code} - Body: {e.response.text}")
        raise HTTPException(status_code=502, detail=f"AI Service Error ({e.response.status_code}). Please try again shortly.")
    except Exception as e:
        logger.exception(f"Unexpected error calling Gemini API. URL was: '{api_url}'")
        raise HTTPException(status_code=500, detail="An internal connection error occurred while reaching the AI service.")

# --- Routes ---
@app.get("/api", summary="Health Check", tags=["General"])
async def health_check():
    return {"status": "SkillSphere API is running!"}

@app.post("/api/register", summary="Register a new user", status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def register(user: UserCreate):
    try:
        if await UserAccount.find_one(UserAccount.email == user.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed_password = get_password_hash(user.password)
        new_user = UserAccount(email=user.email, hashed_password=hashed_password)
        await new_user.insert()
        return {"message": "User registered successfully", "email": new_user.email}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Registration failed")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/api/login", response_model=Token, summary="User Login", tags=["Authentication"])
async def login(form_data: UserLogin):
    try:
        user = await UserAccount.find_one(UserAccount.email == form_data.email)
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        access_token = create_access_token({"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Login failed")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/parse-resume", response_model=ParsedResume, tags=["AI Tools"])
async def parse_resume(request: ResumeParseRequest):
    prompt = f"""
    You are an expert resume parser. Extract the skills, work experience, and education from the resume text below.

    CATEGORIZATION RULES:
    1. Organize skills into logical categories (e.g., Programming Languages, Frameworks, Cloud, Soft Skills).
    2. For experience, strictly separate the "role" (job title) from the "company" name.
    3. Extract "dates" for each experience (e.g., "2020 - Present") and education entry.
    4. The first item in the "experience" list MUST be the most recent or current role.

    FEW-SHOT EXAMPLE:
    Input: "John Doe. Senior Dev at Google (Jan 2020 - Present). Skills: Python, AWS. BS CS from MIT 2022."
    Output:
    {{
      "skills": {{
        "Languages": ["Python"],
        "Cloud": ["AWS"]
      }},
      "experience": [
        {{
          "role": "Senior Developer",
          "company": "Google",
          "dates": "Jan 2020 - Present",
          "summary": "Full-stack development using Python and AWS cloud services."
        }}
      ],
      "education": [
        {{
          "degree": "BS Computer Science",
          "university": "MIT",
          "dates": "2018 - 2022",
          "graduation_year": 2022
        }}
      ]
    }}

    REQUIRED SCHEMA:
    {{
      "skills": {{ "Category Name": ["Skill 1", "Skill 2"] }},
      "experience": [{{ "role": "Title", "company": "Company", "dates": "Period", "summary": "Description" }}],
      "education": [{{ "degree": "Degree", "university": "Uni", "dates": "Period", "graduation_year": YYYY }}]
    }}

    CRITICAL: Return ONLY valid JSON.

    RESUME TEXT:
    ----------------------------------
    {request.resume_text}
    ----------------------------------
    """

    try:
        raw_text = await call_gemini_api(prompt)
    except HTTPException as e:
        logger.warning(f"AI service unavailable (status {e.status_code}), switching to fallback for parsing.")
        fallback_text = fallback_parse_resume(request.resume_text)
        return ParsedResume.model_validate_json(fallback_text)
    except Exception as e:
        logger.exception("Unexpected error during AI parsing call")
        fallback_text = fallback_parse_resume(request.resume_text)
        return ParsedResume.model_validate_json(fallback_text)

    try:
        clean_text = clean_json_response(raw_text)
        return ParsedResume.model_validate_json(clean_text)
    except (ValidationError, json.JSONDecodeError) as e:
        logger.error(f"Validation failed for resume parse: {e}\nAI Response:\n{raw_text}")
        try:
            # Fallback to local parsing if AI response is poorly formatted
            fallback_text = fallback_parse_resume(request.resume_text)
            return ParsedResume.model_validate_json(fallback_text)
        except Exception:
            raise HTTPException(status_code=502, detail="AI returned data in an unexpected format and fallback parsing failed. Please try a different resume formatting.")

@app.post("/api/generate-roadmap", response_model=RoadmapResponse, tags=["AI Tools"])
async def generate_roadmap(request: RoadmapRequest):
    skills_str = ", ".join(request.current_skills)
    prompt = f"""
    You are an elite career coach. Create a detailed learning roadmap.
    
    USER PROFILE:
    - Current Role: {request.current_role}
    - Desired Role: {request.desired_role}
    - Current Skills: {skills_str}
    
    INSTRUCTIONS:
    1. Analyze the User Profile and strictly compare the user's Current Skills with the required skills typically expected for the Desired Role in the industry.
    2. Create a high-impact, step-by-step career roadmap to bridge the gap.
    3. You MUST provide EXACTLY between 5 and 7 steps.
    4. For EACH step, you MUST include 2-3 specific learning resources (e.g., YouTube channels, specific Coursera courses, documentation links).
    5. Ensure the roadmap is tailored to the transition from {request.current_role} to {request.desired_role}.
    6. Include a "Final Mastery Project" suggestion in the last step.
    7. Return ONLY raw JSON matching this exact schema:
    {{
        "skill_gap": {{
            "matching_skills": ["List of current skills that match the desired role"],
            "missing_skills": ["List of skills the user needs to learn for the desired role"]
        }},
        "roadmap": [
            {{
                "step": 1,
                "title": "Step Title",
                "description": "Detailed description of what to learn",
                "resources": ["Resource 1", "Resource 2"]
            }}
        ]
    }}
    """
    
    try:
        raw_text = await call_gemini_api(prompt)
    except HTTPException as e:
        logger.warning(f"AI service unavailable (status {e.status_code}), switching to fallback for roadmap.")
        fallback_text = fallback_generate_roadmap(request.current_role, request.desired_role, request.current_skills)
        return RoadmapResponse.model_validate_json(fallback_text)
    except Exception as e:
        logger.exception("Unexpected error during AI roadmap call")
        fallback_text = fallback_generate_roadmap(request.current_role, request.desired_role, request.current_skills)
        return RoadmapResponse.model_validate_json(fallback_text)
    
    try:
        clean_text = clean_json_response(raw_text)
        return RoadmapResponse.model_validate_json(clean_text)
    except (ValidationError, json.JSONDecodeError) as e:
        logger.error(f"Validation failed for roadmap generation: {e}\nAI Response:\n{raw_text}")
        try:
            fallback_text = fallback_generate_roadmap(request.current_role, request.desired_role, request.current_skills)
            return RoadmapResponse.model_validate_json(fallback_text)
        except Exception:
            raise HTTPException(status_code=422, detail="AI returned data in an unexpected format and fallback failed. Please try again.")

@app.post("/api/roadmaps", status_code=status.HTTP_201_CREATED, tags=["Roadmaps"])
async def save_roadmap(payload: SaveRoadmapPayload, current_user: User = Depends(get_current_user)):
    roadmap = SavedRoadmap(
        user_email=current_user.email, 
        current_role=payload.roadmap_data.current_role, 
        desired_role=payload.roadmap_data.desired_role, 
        skill_gap=payload.roadmap_response.skill_gap,
        roadmap=payload.roadmap_response.roadmap
    )
    await roadmap.insert()
    return {"message": "Roadmap saved successfully", "roadmap_id": str(roadmap.id)}

@app.get("/api/my-roadmaps", response_model=List[SavedRoadmap], tags=["Roadmaps"])
async def get_my_roadmaps(current_user: User = Depends(get_current_user)):
    return await SavedRoadmap.find(SavedRoadmap.user_email == current_user.email).to_list()

@app.delete("/api/roadmaps/{roadmap_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Roadmaps"])
async def delete_roadmap(roadmap_id: PydanticObjectId, current_user: User = Depends(get_current_user)):
    roadmap = await SavedRoadmap.get(roadmap_id)
    if not roadmap: raise HTTPException(status_code=404, detail="Roadmap not found")
    if roadmap.user_email != current_user.email: raise HTTPException(status_code=403, detail="Not authorized")
    await roadmap.delete()
    return None