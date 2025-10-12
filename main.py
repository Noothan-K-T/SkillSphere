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

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Load Environment ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") # <--- CHANGE: Removed default for security
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- FastAPI ---
app = FastAPI(
    title="SkillSphere API",
    description="API for parsing resumes and generating career roadmaps.",
    version="1.0.0"
)

# --- CHANGE: Security enhancement for CORS in production ---
# For development, "*" is fine. For production, list your frontend domains.
# e.g., origins = ["https://your-frontend-app.com", "http://localhost:3000"]
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class Experience(BaseModel):
    role: str
    company: Optional[str] = None
    summary: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def handle_ai_variations(cls, data):
        if isinstance(data, dict):
            if 'title' in data and 'role' not in data:
                data['role'] = data['title']
            if 'description' in data and 'summary' not in data:
                data['summary'] = data['description']
            if 'project' in data.get('role', '').lower() and 'company' not in data:
                data['company'] = 'Personal Project'
        return data

class Education(BaseModel):
    degree: str
    university: str
    graduation_year: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def handle_ai_variations(cls, data):
        if isinstance(data, dict):
            if "university" not in data:
                if "institution" in data:
                    data["university"] = data["institution"]
                elif "location" in data:
                    data["university"] = data["location"]
        return data

class ParsedResume(BaseModel):
    skills: Dict[str, List[str]]
    experience: List[Experience]
    education: List[Education]

class RoadmapStep(BaseModel):
    step: int
    title: str
    description: str
    resources: List[str]

class RoadmapRequest(BaseModel):
    current_role: str = Field(..., example="Junior Python Developer")
    desired_role: str = Field(..., example="Senior Machine Learning Engineer")
    current_skills: List[str] = Field(default=[], example=["Python", "FastAPI", "SQL"])

class RoadmapResponse(BaseModel):
    roadmap: List[RoadmapStep]

class SaveRoadmapPayload(BaseModel):
    roadmap_data: RoadmapRequest
    roadmap_response: RoadmapResponse

class SavedRoadmap(Document):
    user_email: str = Field(..., index=True)
    current_role: str
    desired_role: str
    roadmap: List[RoadmapStep]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "roadmaps"

# --- User Models ---
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

class TokenData(BaseModel):
    email: Optional[str] = None

class User(BaseModel):
    id: PydanticObjectId
    email: EmailStr

    class Config:
        arbitrary_types_allowed = True

class ResumeParseRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)

# --- Auth Setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

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
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await UserAccount.find_one(UserAccount.email == email)
    if user is None:
        raise credentials_exception
    return User(id=user.id, email=user.email)

# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up SkillSphere API...")
    if not MONGO_CONNECTION_STRING:
        raise ValueError("FATAL: MONGO_CONNECTION_STRING is not set in .env file.")
    if not GOOGLE_API_KEY:
        logger.warning("WARNING: GOOGLE_API_KEY is not set. AI features will fail.")
    # <--- CHANGE: Critical security check ---
    if not JWT_SECRET_KEY:
        raise ValueError("FATAL: JWT_SECRET_KEY is not set. This is a major security risk.")

    try:
        logger.info("Connecting to MongoDB...")
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_CONNECTION_STRING)
        await init_beanie(database=client.skillsphere_db, document_models=[UserAccount, SavedRoadmap])
        logger.info("Successfully connected to MongoDB.")
    except Exception as e:
        logger.critical(f"FATAL: Could not connect to MongoDB: {e}")
        raise

# --- Helper Functions ---
# <--- CHANGE: Refactored AI call into a reusable helper ---
async def call_gemini_api(prompt: str, timeout: int = 60) -> str:
    """Calls the Gemini API with a given prompt and returns the text response."""
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="Google API key is not configured on the server.")

# The corrected line
# The corrected, stable version
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GOOGLE_API_KEY}"  
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    try:
        async with AsyncClient() as client:
            resp = await client.post(api_url, json=payload, timeout=timeout)
            resp.raise_for_status()
        data = resp.json()
        if not data.get("candidates"):
            logger.error(f"Invalid AI response structure: {data}")
            raise HTTPException(status_code=502, detail="AI returned an invalid or empty response.")
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except HTTPStatusError as e:
        logger.error(f"HTTP error calling Gemini API: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=502, detail=f"Error communicating with AI service: {e.response.reason_phrase}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while calling Gemini API: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


# --- Routes ---
@app.get("/", summary="Health Check", tags=["General"])
async def health_check():
    """Check if the API is running."""
    return {"status": "SkillSphere API is running!"}

@app.post("/register", summary="Register a new user", status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def register(user: UserCreate):
    """Creates a new user account."""
    if await UserAccount.find_one(UserAccount.email == user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user = UserAccount(email=user.email, hashed_password=hashed_password)
    await new_user.insert()
    return {"message": "User registered successfully", "email": new_user.email}

@app.post("/login", response_model=Token, summary="User Login", tags=["Authentication"])
async def login(form_data: UserLogin):
    """Authenticates a user and returns a JWT access token."""
    user = await UserAccount.find_one(UserAccount.email == form_data.email)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/parse-resume", response_model=ParsedResume, tags=["AI Tools"])
async def parse_resume(request: ResumeParseRequest, current_user: User = Depends(get_current_user)):
    """Parses resume text using AI to extract skills, experience, and education."""
    # <--- CHANGE: Highly specific prompt to ensure valid JSON output ---
    prompt = f"""
    You are an expert resume parser. Your sole task is to analyze the following resume text and convert it into a valid JSON object.
    The JSON object MUST have three top-level keys: "skills", "experience", and "education".

    1.  The "skills" key must map to an object where each key is a skill category (e.g., "Programming Languages", "Databases", "Tools") and the value is a list of skill strings.
    2.  The "experience" key must map to a list of objects. Each object must have "role", "company", and "summary" keys.
    3.  The "education" key must map to a list of objects. Each object must have "degree", "university", and "graduation_year" keys.

    Do not include any introductory text, explanations, or markdown formatting. The output must be only the raw JSON.

    Resume Text:
    ---
    {request.resume_text}
    ---
    """
    parsed_text = await call_gemini_api(prompt)

    # <--- CHANGE: Robust error handling for validation ---
    try:
        return ParsedResume.model_validate_json(parsed_text)
    except (ValidationError, json.JSONDecodeError) as e:
        logger.error(f"Pydantic validation failed for resume parse: {e}\nAI Response was:\n{parsed_text}")
        raise HTTPException(status_code=422, detail="The AI returned data in an unexpected format. Please try again.")

@app.post("/generate-roadmap", response_model=RoadmapResponse, tags=["AI Tools"])
async def generate_roadmap(request: RoadmapRequest, current_user: User = Depends(get_current_user)):
    """Generates a career roadmap using AI based on current and desired roles."""
    # <--- CHANGE: More structured prompt for roadmap generation ---
    prompt = f"""
    Create a detailed, step-by-step learning roadmap for a professional aiming to transition from a "{request.current_role}" to a "{request.desired_role}".
    The user's current skills are: {', '.join(request.current_skills) if request.current_skills else 'None listed'}.

    Your response must be a single, valid JSON object with a single top-level key: "roadmap".
    The "roadmap" key must map to a list of step objects.
    Each step object in the list must contain the following keys:
    - "step": An integer representing the order of the step (starting from 1).
    - "title": A concise string title for the step.
    - "description": A string explaining what to learn or do in this step.
    - "resources": A list of strings, where each string is a suggested resource (e.g., a book title, online course, or technology to practice).

    Generate a practical and logical roadmap. The output must be only the raw JSON.
    """
    parsed_text = await call_gemini_api(prompt)

    # <--- CHANGE: Robust error handling for validation ---
    try:
        return RoadmapResponse.model_validate_json(parsed_text)
    except (ValidationError, json.JSONDecodeError) as e:
        logger.error(f"Pydantic validation failed for roadmap generation: {e}\nAI Response was:\n{parsed_text}")
        raise HTTPException(status_code=422, detail="The AI returned data in an unexpected format. Please try again.")


@app.post("/roadmaps", summary="Save a generated roadmap", status_code=status.HTTP_201_CREATED, tags=["Roadmaps"])
async def save_roadmap(payload: SaveRoadmapPayload, current_user: User = Depends(get_current_user)):
    """Saves a user's generated roadmap to their profile."""
    roadmap = SavedRoadmap(
        user_email=current_user.email,
        current_role=payload.roadmap_data.current_role,
        desired_role=payload.roadmap_data.desired_role,
        roadmap=payload.roadmap_response.roadmap,
    )
    await roadmap.insert()
    return {"message": "Roadmap saved successfully", "roadmap_id": str(roadmap.id)}

@app.get("/my-roadmaps", response_model=List[SavedRoadmap], tags=["Roadmaps"])
async def get_my_roadmaps(current_user: User = Depends(get_current_user)):
    """Retrieves all roadmaps saved by the current user."""
    return await SavedRoadmap.find(SavedRoadmap.user_email == current_user.email).to_list()

@app.delete("/roadmaps/{roadmap_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Roadmaps"])
async def delete_roadmap(roadmap_id: PydanticObjectId, current_user: User = Depends(get_current_user)):
    """Deletes a specific roadmap saved by the current user."""
    roadmap = await SavedRoadmap.get(roadmap_id)
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    if roadmap.user_email != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized to delete this roadmap")
    await roadmap.delete()
    return None

# --- Run App ---
if __name__ == "__main__":
    import uvicorn
    # Note: The port is set to 8001 as in the original snippet.
    # The app object should be specified as "main:app" if the file is named main.py
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)