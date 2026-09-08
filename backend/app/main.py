from fastapi import FastAPI
from .api import risk

app = FastAPI(title="FloodIntel API", version="1.0.0")

app.include_router(risk.router, prefix="/api/v1/risk", tags=["risk"])

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "FloodIntel"}
