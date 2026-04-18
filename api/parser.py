import pdfplumber
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import json

from api.ai_utils import call_ai, clean_json_response

router = APIRouter()


class Experience(BaseModel):
    role: str
    company: str
    summary: str


class Education(BaseModel):
    degree: str
    university: str
    graduation_year: int | None = None


class ParsedResume(BaseModel):
    raw_text: str
    skills: Dict[str, List[str]]
    experience: List[Experience]
    education: List[Education]


def extract_pdf_text(file) -> str:
    try:
        with pdfplumber.open(file) as pdf:
            text = "\n".join([(page.extract_text() or "") for page in pdf.pages])
        return text.strip()
    except:
        raise HTTPException(status_code=500, detail="Failed to read PDF file.")


def build_prompt(resume_text: str) -> str:
    return f"""
You are an ATS-grade resume parser. Extract structured data.

RETURN STRICT RAW JSON ONLY.
NO MARKDOWN. NO COMMENTS.

SCHEMA:
{{
  "skills": {{
      "languages": [],
      "frameworks": [],
      "tools": [],
      "other": []
  }},
  "experience": [
    {{
      "role": "",
      "company": "",
      "summary": ""
    }}
  ],
  "education": [
    {{
      "degree": "",
      "university": "",
      "graduation_year": 0
    }}
  ]
}}

RESUME:
---------------------------------------
{resume_text}
---------------------------------------
"""


@router.post("/upload", response_model=ParsedResume)
async def upload_resume(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed.")

    text = extract_pdf_text(file.file)

    prompt = build_prompt(text)
    raw_output = await call_ai(prompt)

    cleaned = clean_json_response(raw_output)

    try:
        parsed = json.loads(cleaned)
    except Exception:
        raise HTTPException(status_code=500, detail="AI returned invalid JSON.")

    return ParsedResume(
        raw_text=text,
        skills=parsed.get("skills", {}),
        experience=parsed.get("experience", []),
        education=parsed.get("education", [])
    )
