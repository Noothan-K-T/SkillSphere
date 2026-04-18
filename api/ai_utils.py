# /api/ai_utils.py

import os
import json
import logging
from httpx import AsyncClient, HTTPStatusError
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if OPENROUTER_API_KEY:
    print("✅ OpenRouter Key Loaded")
else:
    print("❌ OPENROUTER_API_KEY missing in .env")


# ----------------------------------------------------
# CLEAN JSON RESPONSE
# ----------------------------------------------------
def clean_json_response(text: str) -> str:
    """Remove ```json or ``` blocks returned by AI."""
    text = text.strip()

    if text.startswith("```json"):
        text = text[len("```json"):]

    if text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


# ----------------------------------------------------
# MAIN AI CALL (OpenRouter)
# ----------------------------------------------------
async def call_ai(prompt: str) -> str:
    """
    Calls OpenRouter using a free model.
    """

    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenRouter API key not configured")

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
    "model": "mistralai/mistral-7b-instruct",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.2,
    "max_tokens": 500
}


    try:
        async with AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()

        data = resp.json()
        return data["choices"][0]["message"]["content"]

    except HTTPStatusError as e:
        logger.error(f"OpenRouter API Error: {e.response.text}")
        raise HTTPException(status_code=500, detail=f"AI service failed: {e.response.text}")

    except Exception as e:
        print("RAW ERROR:", e)   # 👈 IMPORTANT
        raise HTTPException(status_code=500, detail=f"Unexpected AI error: {str(e)}")

