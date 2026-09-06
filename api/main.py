from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers.assistant import router as assistant_router
from api.routers.flood import router as flood_router
from api.services.assistant_service import (
    SUPPORTED_LANGUAGES,
    get_ollama_status,
)
from api.services.flood_service import load_flood_summary
from api.services.model_service import get_model_metadata


APP_NAME = "FloodIntel API"
APP_VERSION = "2.1.0"


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "Backend API for FloodIntel — AI-Powered Flood Intelligence "
        "and Early Warning Platform."
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(flood_router)
app.include_router(assistant_router)


@app.get("/")
async def root():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "online",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health")
async def health():
    flood_data_available = True

    try:
        load_flood_summary()
    except (FileNotFoundError, ValueError):
        flood_data_available = False

    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "flood_data_available": flood_data_available,
    }


@app.get("/api/languages")
async def languages():
    return {
        "status": "success",
        "count": len(SUPPORTED_LANGUAGES),
        "languages": SUPPORTED_LANGUAGES,
    }


@app.get("/api/system/info")
async def system_info():
    ollama = get_ollama_status()
    model = get_model_metadata()

    flood_data_available = True

    try:
        summary = load_flood_summary()
    except (FileNotFoundError, ValueError):
        summary = None
        flood_data_available = False

    return {
        "status": "success",
        "application": {
            "name": APP_NAME,
            "version": APP_VERSION,
        },
        "services": {
            "flood_data": {
                "available": flood_data_available,
            },
            "ollama": ollama,
            "model": model,
        },
        "supported_languages": SUPPORTED_LANGUAGES,
        "prediction_source": (
            summary.get("source", "precomputed_flood_prediction")
            if isinstance(summary, dict)
            else "precomputed_flood_prediction"
        ),
    }