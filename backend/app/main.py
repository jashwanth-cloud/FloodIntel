import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import risk, forecast, weather, satellite, alerts, intelligence

load_dotenv()
app = FastAPI(title="FloodIntel API", version="1.0.0")

# CORS configuration
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(risk.router, prefix="/api/v1/risk", tags=["risk"])
app.include_router(forecast.router, prefix="/api/v1/forecast", tags=["forecast"])
app.include_router(weather.router, prefix="/api/v1/weather", tags=["weather"])
app.include_router(satellite.router, prefix="/api/v1", tags=["satellite"])
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
app.include_router(intelligence.router, prefix="/api/v1", tags=["intelligence"])

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "FloodIntel"}
