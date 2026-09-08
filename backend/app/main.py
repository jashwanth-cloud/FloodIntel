from fastapi import FastAPI
from .api import risk, forecast

app = FastAPI(title="FloodIntel API", version="1.0.0")

app.include_router(risk.router, prefix="/api/v1/risk", tags=["risk"])
app.include_router(forecast.router, prefix="/api/v1/forecast", tags=["forecast"])

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "FloodIntel"}
