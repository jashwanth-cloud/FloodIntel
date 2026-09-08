from fastapi import APIRouter
from ..services.rainfall_service import IMDHistoricalRainfallProvider, DemoRainfallProvider, DataUnavailableError
from ..services.risk_engine_service import RiskEngineService

router = APIRouter()

@router.get("/{location_id}")
async def get_risk(location_id: int):
    # Try IMD first
    try:
        rainfall_data = IMDHistoricalRainfallProvider().get_latest_rainfall(location_id)
    except DataUnavailableError:
        # Fallback to Demo
        rainfall_data = DemoRainfallProvider().get_latest_rainfall(location_id)
        
    risk_engine = RiskEngineService()
    risk_assessment = risk_engine.calculate_risk(location_id, rainfall_data)
    
    return risk_assessment
