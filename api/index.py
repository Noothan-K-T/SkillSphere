# /api/index.py

import os
import logging
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status
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
load_dotenv()

# --- Environment Variables & Constants ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- FastAPI App ---
app = FastAPI(
    title="SkillSphere API",
    description="API for parsing resumes and generating career roadmaps.",
    version="1.0.0",
    # Hide docs in production on Vercel
    docs_url="/docs" if os.getenv("VERCEL_ENV") != "production" else None,
    redoc_url="/redoc" if os.getenv("VERCEL_ENV") != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Database Client ---
# Create client at global scope for reuse across function invocations
if not MONGO_CONNECTION_STRING:
    logger.error("FATAL: MONGO_CONNECTION_STRING is not set.")
    # You might want to handle this differently, but for Vercel, env vars are critical
    # This will cause the deployment to fail if the env var is missing, which is good.
    raise ValueError("MONGO_CONNECTION_STRING environment variable not set.")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_CONNECTION_STRING)

# --- NEW: Database Initialization as a Dependency ---
# This replaces the @app.on_event("startup") which doesn't work in serverless
async def init_db():
    """Dependency to initialize Beanie ODM."""
    try:
        await init_beanie(
            database=client.skillsphere_db,
            document_models=[UserAccount, SavedRoadmap]
        )
    except Exception as e:
        logger.error(f"Error initializing Beanie: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed.")

# --- Models (No changes, condensed for brevity) ---
class Experience(BaseModel):
    role: str; company: Optional[str] = None; summary: Optional[str] = None
    @model_validator(mode='before')
    @classmethod
    def handle_ai_variations(cls, data):
        if isinstance(data, dict):
            if 'title' in data and 'role' not in data: data['role'] = data['title']
            if 'description' in data and 'summary' not in data: data['summary'] = data['description']
            if 'project' in data.get('role', '').lower() and 'company' not in data: data['company'] = 'Personal Project'
        return data

class Education(BaseModel):
    degree: str; university: str; graduation_year: Optional[int] = None
    @model_validator(mode="before")
    @classmethod
    def handle_ai_variations(cls, data):
        if isinstance(data, dict):
            if "university" not in data:
                if "institution" in data: data["university"] = data["institution"]
                elif "location" in data: data["university"] = data["location"]
        return data

class ParsedResume(BaseModel):
    skills: Dict[str, List[str]]; experience: List[Experience]; education: List[Education]

class RoadmapStep(BaseModel):
    step: int; title: str; description: str; resources: List[str]

class RoadmapRequest(BaseModel):
    current_role: str = Field(..., example="Junior Python Developer"); desired_role: str = Field(..., example="Senior Machine Learning Engineer"); current_skills: List[str] = Field(default=[], example=["Python", "FastAPI", "SQL"])

class RoadmapResponse(BaseModel):
    roadmap: List[RoadmapStep]

class SaveRoadmapPayload(BaseModel):
    roadmap_data: RoadmapRequest; roadmap_response: RoadmapResponse

class SavedRoadmap(Document):
    user_email: str = Field(..., index=True); current_role: str; desired_role: str; roadmap: List[RoadmapStep]; created_at: datetime = Field(default_factory=datetime.utcnow)
    class Settings: name = "roadmaps"

class UserAccount(Document):
    email: EmailStr = Field(..., unique=True); hashed_password: str; created_at: datetime = Field(default_factory=datetime.utcnow)
    class Settings: name = "users"

class UserCreate(BaseModel):
    email: EmailStr; password: str = Field(..., min_length=8, max_length=72)

class UserLogin(BaseModel):
    email: EmailStr; password: str

class Token(BaseModel):
    access_token: str; token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class User(BaseModel):
    id: PydanticObjectId; email: EmailStr
    class Config: arbitrary_types_allowed = True

class ResumeParseRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)


# --- Auth Setup ---
# All paths must be prefixed for Vercel routing
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str: return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool: return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    if not JWT_SECRET_KEY: raise HTTPException(status_code=500, detail="JWT Secret Key not configured")
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await UserAccount.find_one(UserAccount.email == email)
    if user is None: raise credentials_exception
    return User(id=user.id, email=user.email)

# --- Helper Functions ---
async def call_gemini_api(prompt: str, timeout: int = 60) -> str:
    if not GOOGLE_API_KEY: raise HTTPException(status_code=500, detail="Google API key is not configured.")
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GOOGLE_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json"}}
    try:
        async with AsyncClient() as client:
            resp = await client.post(api_url, json=payload, timeout=timeout)
            resp.raise_for_status()
        data = resp.json()
        if not data.get("candidates"): raise HTTPException(status_code=502, detail="AI returned an invalid response.")
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except HTTPStatusError as e:
        logger.error(f"HTTP error calling Gemini API: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=502, detail=f"Error communicating with AI service.")
    except Exception as e:
        logger.error(f"Unexpected error calling Gemini API: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

# --- Routes ---
@app.get("/api", summary="Health Check", tags=["General"])
async def health_check():
    return {"status": "SkillSphere API is running!"}

# All DB-related endpoints now depend on init_db
@app.post("/api/register", summary="Register a new user", status_code=status.HTTP_201_CREATED, tags=["Authentication"], dependencies=[Depends(init_db)])
async def register(user: UserCreate):
    if await UserAccount.find_one(UserAccount.email == user.email): raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user = UserAccount(email=user.email, hashed_password=hashed_password)
    await new_user.insert()
    return {"message": "User registered successfully", "email": new_user.email}

@app.post("/api/login", response_model=Token, summary="User Login", tags=["Authentication"], dependencies=[Depends(init_db)])
async def login(form_data: UserLogin):
    user = await UserAccount.find_one(UserAccount.email == form_data.email)
    if not user or not verify_password(form_data.password, user.hashed_password): raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/parse-resume", response_model=ParsedResume, tags=["AI Tools"], dependencies=[Depends(init_db)])
async def parse_resume(request: ResumeParseRequest, current_user: User = Depends(get_current_user)):
    prompt = f"""You are an expert resume parser...""" # Your detailed prompt
    parsed_text = await call_gemini_api(prompt)
    try:
        return ParsedResume.model_validate_json(parsed_text)
    except (ValidationError, json.JSONDecodeError) as e:
        logger.error(f"Pydantic validation failed for resume parse: {e}\nAI Response:\n{parsed_text}")
        raise HTTPException(status_code=422, detail="AI returned data in an unexpected format.")

@app.post("/api/generate-roadmap", response_model=RoadmapResponse, tags=["AI Tools"], dependencies=[Depends(init_db)])
async def generate_roadmap(request: RoadmapRequest, current_user: User = Depends(get_current_user)):
    prompt = f"""Create a detailed, step-by-step learning roadmap...""" # Your detailed prompt
    parsed_text = await call_gemini_api(prompt)
    try:
        return RoadmapResponse.model_validate_json(parsed_text)
    except (ValidationError, json.JSONDecodeError) as e:
        logger.error(f"Pydantic validation failed for roadmap generation: {e}\nAI Response:\n{parsed_text}")
        raise HTTPException(status_code=422, detail="AI returned data in an unexpected format.")

@app.post("/api/roadmaps", status_code=status.HTTP_201_CREATED, tags=["Roadmaps"], dependencies=[Depends(init_db)])
async def save_roadmap(payload: SaveRoadmapPayload, current_user: User = Depends(get_current_user)):
    roadmap = SavedRoadmap(user_email=current_user.email, current_role=payload.roadmap_data.current_role, desired_role=payload.roadmap_data.desired_role, roadmap=payload.roadmap_response.roadmap)
    await roadmap.insert()
    return {"message": "Roadmap saved successfully", "roadmap_id": str(roadmap.id)}

@app.get("/api/my-roadmaps", response_model=List[SavedRoadmap], tags=["Roadmaps"], dependencies=[Depends(init_db)])
async def get_my_roadmaps(current_user: User = Depends(get_current_user)):
    return await SavedRoadmap.find(SavedRoadmap.user_email == current_user.email).to_list()

@app.delete("/api/roadmaps/{roadmap_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Roadmaps"], dependencies=[Depends(init_db)])
async def delete_roadmap(roadmap_id: PydanticObjectId, current_user: User = Depends(get_current_user)):
    roadmap = await SavedRoadmap.get(roadmap_id)
    if not roadmap: raise HTTPException(status_code=404, detail="Roadmap not found")
    if roadmap.user_email != current_user.email: raise HTTPException(status_code=403, detail="Not authorized")
    await roadmap.delete()
    return None