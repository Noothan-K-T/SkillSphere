import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field, EmailStr, model_validator
import httpx
from typing import List, Dict, Optional
from beanie import Document, init_beanie, PydanticObjectId
import motor.motor_asyncio

from fastapi.middleware.cors import CORSMiddleware
# --- Database Imports ---
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# --- Security Imports ---
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Environment Setup ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "a_very_secret_key_that_should_be_in_env")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# --- Pydantic & Beanie Models ---

class Experience(BaseModel):
    role: str
    company: str
    summary: str

    @model_validator(mode='before')
    @classmethod
    def handle_ai_variations(cls, data):
        if isinstance(data, dict):
            if 'title' in data and 'role' not in data: data['role'] = data['title']
            if 'description' in data and 'summary' not in data: data['summary'] = data['description']
        return data


class Education(BaseModel):
    degree: str
    university: str
    graduation_year: Optional[int] = None

    @model_validator(mode='before')
    @classmethod
    def handle_ai_variations(cls, data):
        if isinstance(data, dict):
            if 'university' not in data:
                if 'institution' in data:
                    data['university'] = data['institution']
                elif 'location' in data:
                    data['university'] = data['location']
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
    current_role: str = Field(..., min_length=2)
    desired_role: str = Field(..., min_length=2)
    current_skills: List[str] = []


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
    id: str
    email: EmailStr


class ResumeParseRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)


# --- Startup Event Handler ---
async def startup_db_clients():
    # PostgreSQL setup
    try:
        migration_file = "database/migrations/001_create_users_table.sql"
        logger.info("Ensuring PostgreSQL schema is up to date...")
        if os.path.exists(migration_file):
            async with postgres_engine.begin() as conn:
                await conn.execute(text(open(migration_file).read()))
            logger.info("PostgreSQL schema is ready.")
        else:
            logger.warning(f"PostgreSQL migration file not found at {migration_file}. Skipping schema setup.")
    except Exception as e:
        logger.error(f"An error occurred during PostgreSQL schema setup: {e}")

    # MongoDB setup
    try:
        logger.info("Connecting to MongoDB...")
        if not MONGO_CONNECTION_STRING:
            raise ValueError("MONGO_CONNECTION_STRING is not set in .env file")
        mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_CONNECTION_STRING)
        await init_beanie(database=mongo_client.skillsphere_db, document_models=[SavedRoadmap])
        logger.info("Successfully connected to MongoDB.")
    except Exception as e:
        logger.error(f"An error occurred during MongoDB connection: {e}")


# --- FastAPI Application ---
app = FastAPI(title="SkillSphere API")
app.add_event_handler("startup", startup_db_clients)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Setup ---
postgres_engine = create_async_engine(DATABASE_URL)
AsyncPostgresSessionLocal = sessionmaker(postgres_engine, class_=AsyncSession, expire_on_commit=False)


# --- Dependencies ---
async def get_postgres_db():
    async with AsyncPostgresSessionLocal() as session:
        yield session


# --- Security Functions ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_postgres_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = await get_user_by_email(db, email=token_data.email)
    if user is None: raise credentials_exception
    return user


# --- Database CRUD Functions ---
async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(text("SELECT id, email, hashed_password FROM users WHERE email = :email"),
                              {"email": email})
    return result.mappings().first()


async def create_user(db: AsyncSession, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    query = text(
        "INSERT INTO users (email, hashed_password) VALUES (:email, :hashed_password) RETURNING id, email, created_at")
    result = await db.execute(query, {"email": user.email, "hashed_password": hashed_password})
    await db.commit()
    return result.mappings().first()


# --- API Endpoints ---
@app.get("/", summary="Health Check")
async def read_root():
    return {"status": "SkillSphere API is running!"}


@app.post("/register", summary="Register a new user")
async def register(user: UserCreate, db: AsyncSession = Depends(get_postgres_db)):
    db_user = await get_user_by_email(db, email=user.email)
    if db_user: raise HTTPException(status_code=400, detail="Email already registered")
    new_user = await create_user(db, user=user)
    return {"message": "User created successfully", "user": {"id": new_user['id'], "email": new_user['email']}}


@app.post("/login", response_model=Token, summary="User Login")
async def login(form_data: UserLogin, db: AsyncSession = Depends(get_postgres_db)):
    user = await get_user_by_email(db, email=form_data.email)
    if not user or not verify_password(form_data.password, user['hashed_password']):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user['email']})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/parse-resume", response_model=ParsedResume, summary="Parse a Resume (Requires Auth)")
async def parse_resume(request: ResumeParseRequest, current_user: User = Depends(get_current_user)):
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="Google API key is not configured.")
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={GOOGLE_API_KEY}"

    prompt = f"""
    You are an expert resume parser for SkillSphere. Analyze the following resume text.
    Return ONLY a valid JSON object with three keys: "skills", "experience", and "education".
    - "skills": An object where keys are skill categories (e.g., "Programming Languages", "Tools") and values are arrays of strings.
    - "experience": An array of objects, each with "role", "company", and "summary".
    - "education": An array of objects, each with "degree", "university", and "graduation_year" (an integer, or null if not found).
    Do not include any other text or markdown.

    Resume Text:
    ---
    {request.resume_text}
    ---
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}],
               "generationConfig": {"responseMimeType": "application/json"}}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_url, json=payload, timeout=45.0)
            response.raise_for_status()
            result = response.json()
            if result.get("candidates"):
                parsed_text = result["candidates"][0]["content"]["parts"][0]["text"]
                return ParsedResume.model_validate_json(parsed_text)
            else:
                raise HTTPException(status_code=500, detail="AI service returned an invalid response.")
        except Exception as e:
            logger.error(f"Error during resume parsing: {e}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.post("/generate-roadmap", response_model=RoadmapResponse, summary="Generate Career Roadmap (Requires Auth)")
async def generate_roadmap(request: RoadmapRequest, current_user: User = Depends(get_current_user)):
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="Google API key is not configured.")

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={GOOGLE_API_KEY}"
    current_skills_str = ", ".join(request.current_skills) if request.current_skills else "None"

    prompt = f"""
    Act as an expert career coach for the SkillSphere platform. A user wants to transition from
    their current role of '{request.current_role}' to a new role of '{request.desired_role}'.
    The user already possesses the following skills: {current_skills_str}.

    Your task is to generate a concise, step-by-step learning roadmap.

    IMPORTANT: The output MUST be a valid JSON object and NOTHING else. Do not include any introductory text, explanations, or markdown formatting like ```json.

    The JSON object must have a single key "roadmap", which is an array of objects.
    Each object in the array represents a step and must have these four keys:
    1. "step": (Integer) The step number, starting from 1.
    2. "title": (String) A short, clear title for the step.
    3. "description": (String) A 1-2 sentence explanation of why this step is important, focusing on filling skill gaps.
    4. "resources": (Array of Strings) A list of 2-3 specific, high-quality learning resources.

    Create a roadmap with 5 to 7 logical steps. Do not suggest skills the user already has.
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}],
               "generationConfig": {"responseMimeType": "application/json"}}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_url, json=payload, timeout=60.0)
            response.raise_for_status()
            result = response.json()
            if result.get("candidates"):
                parsed_text = result["candidates"][0]["content"]["parts"][0]["text"]
                return RoadmapResponse.model_validate_json(parsed_text)
            else:
                raise HTTPException(status_code=500, detail="AI service returned an invalid response for roadmap.")
        except Exception as e:
            logger.error(f"Error during roadmap generation: {e}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.post("/roadmaps", status_code=status.HTTP_201_CREATED, summary="Save a Generated Roadmap (Requires Auth)")
async def save_roadmap(payload: SaveRoadmapPayload, current_user: User = Depends(get_current_user)):
    saved_roadmap = SavedRoadmap(
        user_email=current_user.email,
        current_role=payload.roadmap_data.current_role,
        desired_role=payload.roadmap_data.desired_role,
        roadmap=payload.roadmap_response.roadmap
    )
    await saved_roadmap.insert()
    return {"message": "Roadmap saved successfully!", "roadmap_id": str(saved_roadmap.id)}


@app.get("/my-roadmaps", response_model=List[SavedRoadmap], summary="Get All Saved Roadmaps for a User (Requires Auth)")
async def get_my_roadmaps(current_user: User = Depends(get_current_user)):
    roadmaps = await SavedRoadmap.find(SavedRoadmap.user_email == current_user.email).to_list()
    return roadmaps


# --- NEW DELETE ENDPOINT ---
@app.delete("/roadmaps/{roadmap_id}", status_code=status.HTTP_204_NO_CONTENT,
            summary="Delete a Saved Roadmap (Requires Auth)")
async def delete_roadmap(roadmap_id: PydanticObjectId, current_user: User = Depends(get_current_user)):
    """
    Deletes a specific roadmap by its ID, ensuring it belongs to the current user.
    """
    roadmap_to_delete = await SavedRoadmap.get(roadmap_id)
    if not roadmap_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")

    if roadmap_to_delete.user_email != current_user.email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this roadmap")

    await roadmap_to_delete.delete()
    return None  # Return no content on successful deletion

