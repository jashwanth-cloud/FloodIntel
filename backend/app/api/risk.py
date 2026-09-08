from fastapi import APIRouter
from ..services.rainfall_service import IMDHistoricalRainfallProvider, DemoRainfallProvider, DataUnavailableError
from ..services.risk_engine_service import RiskEngineService
from datetime import datetime

router = APIRouter()

@router.get("/{location_id}")
async def get_risk(location_id: int):
    # Hardcoded coordinates for demo location 1 (e.g., Visakhapatnam area)
    lat, lon = 17.7, 83.3
    timestamp = datetime(2025, 8, 15)
    
    # Try IMD first
    try:
        rainfall_provider = IMDHistoricalRainfallProvider()
        rainfall_data = rainfall_provider.get_rainfall(lat, lon, timestamp)
    except Exception as e: # Broad catch for DataUnavailableError or file reading issues
        print(f"IMD Provider failed: {e}")
        # Fallback to Demo
        rainfall_data = DemoRainfallProvider().get_rainfall(lat, lon, timestamp)
        
    risk_engine = RiskEngineService()
    # Simple defaults for demo
    risk_assessment = risk_engine.calculate_risk(location_id, rainfall_data, lag_1=0.0, rolling_mean_3=rainfall_data.get("amount", 0))
    
    return risk_assessment
