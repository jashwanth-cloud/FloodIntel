from pathlib import Path
import json
from typing import Optional

import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api.routers.flood import router as flood_router


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "Flood Intelligence API"
APP_VERSION = "2.0.0"

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b"

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

FLOOD_SUMMARY_FILE = PROCESSED_DIR / "flood_prediction_summary.json"


SUPPORTED_LANGUAGES = {
    "en": "English",
    "te": "Telugu",
    "hi": "Hindi",
    "ta": "Tamil",
    "kn": "Kannada",
    "ml": "Malayalam",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "or": "Odia",
    "ur": "Urdu",
}


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="AI-powered flood intelligence and early warning API",
)


# ============================================================
# ROUTER REGISTRATION
# ============================================================

app.include_router(flood_router)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def load_flood_summary():
    """Load the processed flood prediction summary."""

    if not FLOOD_SUMMARY_FILE.exists():
        raise FileNotFoundError(
            f"Flood prediction summary not found: {FLOOD_SUMMARY_FILE}"
        )

    try:
        with FLOOD_SUMMARY_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid flood prediction summary JSON: {exc}"
        ) from exc


def check_ollama():
    """Check whether Ollama is running."""

    try:
        response = requests.get(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=3,
        )

        if response.status_code != 200:
            return False

        models = response.json().get("models", [])

        for model in models:
            if model.get("name") == OLLAMA_MODEL:
                return True

        return False

    except requests.RequestException:
        return False


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
        "message": "FloodIntel backend is running",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
    }


# ============================================================
# FLOOD SUMMARY
# ============================================================

@app.get("/flood/summary")
async def flood_summary():

    try:

        summary = load_flood_summary()

        return {
            "status": "success",
            "data": summary,
        }

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# FLOOD STATUS
# ============================================================

@app.get("/flood/status")
async def flood_status():

    try:

        summary = load_flood_summary()

        prediction = summary.get("prediction", {})
        risk = summary.get("risk", {})
        area = summary.get("area", {})

        return {
            "status": "success",
            "flood_status": prediction.get(
                "status",
                prediction.get("label", "Unknown"),
            ),
            "risk_level": risk.get(
                "level",
                risk.get("risk_level", "Unknown"),
            ),
            "affected_area": area,
        }

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# FLOOD ADVISORY
# ============================================================

@app.get("/flood/advisory")
async def flood_advisory():

    try:

        summary = load_flood_summary()

        prediction = summary.get("prediction", {})
        risk = summary.get("risk", {})

        risk_level = risk.get(
            "level",
            risk.get("risk_level", "Unknown"),
        )

        if str(risk_level).lower() == "high":

            advisory = (
                "High flood risk detected. "
                "Avoid low-lying and waterlogged areas "
                "and follow official emergency instructions."
            )

        elif str(risk_level).lower() == "medium":

            advisory = (
                "Moderate flood risk detected. "
                "Stay alert and monitor rainfall and official alerts."
            )

        else:

            advisory = (
                "No immediate high flood risk indicated "
                "by the current prediction summary."
            )

        return {
            "status": "success",
            "risk_level": risk_level,
            "prediction": prediction,
            "advisory": advisory,
        }

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# FLOOD STATISTICS
# ============================================================

@app.get("/flood/statistics")
async def flood_statistics():

    try:

        summary = load_flood_summary()

        return {
            "status": "success",
            "statistics": summary.get(
                "statistics",
                summary.get("area", {}),
            ),
        }

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# FLOOD VALIDATION
# ============================================================

@app.get("/flood/validation")
async def flood_validation():

    try:

        summary = load_flood_summary()

        return {
            "status": "success",
            "validation": summary.get(
                "validation",
                {},
            ),
        }

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# LANGUAGES
# ============================================================

@app.get("/languages")
async def languages():

    return {
        "status": "success",
        "count": len(SUPPORTED_LANGUAGES),
        "languages": SUPPORTED_LANGUAGES,
    }


# ============================================================
# AI ASSISTANT
# ============================================================

@app.get("/assistant")
async def assistant(
    message: str = Query(..., min_length=1),
    language: str = Query("en"),
):

    if language not in SUPPORTED_LANGUAGES:

        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language: {language}",
        )

    ollama_available = check_ollama()

    if not ollama_available:

        return {
            "status": "unavailable",
            "message": (
                "AI assistant is currently unavailable. "
                "Please make sure Ollama is running."
            ),
            "model": OLLAMA_MODEL,
            "language": SUPPORTED_LANGUAGES[language],
        }

    try:

        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": message,
                "stream": False,
            },
            timeout=60,
        )

        response.raise_for_status()

        result = response.json()

        return {
            "status": "success",
            "response": result.get("response", ""),
            "model": OLLAMA_MODEL,
            "language": SUPPORTED_LANGUAGES[language],
        }

    except requests.RequestException as exc:

        raise HTTPException(
            status_code=503,
            detail=f"Ollama request failed: {exc}",
        )


# ============================================================
# SYSTEM INFORMATION
# ============================================================

@app.get("/system/info")
async def system_info():

    ollama_running = check_ollama()

    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "ollama": {
            "running": ollama_running,
            "base_url": OLLAMA_BASE_URL,
            "model": OLLAMA_MODEL,
        },
        "paths": {
            "project_root": str(PROJECT_ROOT),
            "data": str(DATA_DIR),
            "processed": str(PROCESSED_DIR),
            "raw": str(RAW_DIR),
        },
        "languages": {
            "count": len(SUPPORTED_LANGUAGES),
            "supported": SUPPORTED_LANGUAGES,
        },
    }