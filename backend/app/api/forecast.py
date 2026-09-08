from fastapi import APIRouter
from ..services.rainfall_service import IMDHistoricalRainfallProvider, DemoRainfallProvider, DataUnavailableError
from ..ml.forecaster import RainfallForecaster
from datetime import datetime

router = APIRouter()

@router.get("/{location_id}")
async def get_forecast(location_id: int):
    # Hardcoded coordinates for demo location 1 (e.g., Visakhapatnam area)
    lat, lon = 17.7, 83.3
    timestamp = datetime(2025, 8, 15)
    
    # Try IMD
    try:
        rainfall_provider = IMDHistoricalRainfallProvider()
        rainfall_data = rainfall_provider.get_rainfall(lat, lon, timestamp)
        # Simplified features for forecast inference (needs more context for accurate lag_1/rolling)
        lag_1 = 0.0
        rolling_mean = rainfall_data.get("amount", 0)
    except Exception:
        # Fallback to Demo
        rainfall_data = DemoRainfallProvider().get_rainfall(lat, lon, timestamp)
        lag_1 = 0.0
        rolling_mean = rainfall_data.get("amount", 0)
        
    forecaster = RainfallForecaster()
    forecast = forecaster.forecast(rainfall_data.get("amount", 0), lag_1, rolling_mean)
    
    return {**rainfall_data, **forecast}
