from fastapi import APIRouter
from ..services.providers.weather_provider import IMDWeatherProvider

router = APIRouter()

@router.get("/{location_id}")
async def get_weather(location_id: int):
    # Hardcoded coordinates for demo location 1 (e.g., Visakhapatnam area)
    lat, lon = 17.7, 83.3
    
    provider = IMDWeatherProvider()
    weather_data = await provider.get_current_weather(lat, lon)
    
    return {
        "location_id": location_id,
        "latitude": lat,
        "longitude": lon,
        **weather_data
    }
