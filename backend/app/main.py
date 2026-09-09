from fastapi import FastAPI
from .api import risk, forecast, weather, satellite, alerts, intelligence

app = FastAPI(title="FloodIntel API", version="1.0.0")

app.include_router(risk.router, prefix="/api/v1/risk", tags=["risk"])
app.include_router(forecast.router, prefix="/api/v1/forecast", tags=["forecast"])
app.include_router(weather.router, prefix="/api/v1/weather", tags=["weather"])
app.include_router(satellite.router, prefix="/api/v1", tags=["satellite"])
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
app.include_router(intelligence.router, prefix="/api/v1", tags=["intelligence"])

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "FloodIntel"}
