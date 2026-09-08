from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class RiskFactor(BaseModel):
    factor: str
    impact: str
    value: float
    unit: str
    description: str

class RiskAssessment(BaseModel):
    location_id: int
    timestamp: str
    risk_score: int
    risk_level: str
    factors: List[RiskFactor]
    model_version: str
    data_state: str
