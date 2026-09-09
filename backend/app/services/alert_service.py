from typing import Dict, Any, List
from .risk_engine_service import RiskEngineService
from backend.app.ml.forecaster import RainfallForecaster
from backend.app.services.providers.weather_provider import IMDWeatherProvider
from backend.app.geospatial.raster_utils import get_raster_metadata
from datetime import datetime, timezone

class AlertEngineService:
    def __init__(self):
        self._risk_service = None
        self._forecaster = None
        self._weather_provider = None
        
    @property
    def risk_service(self):
        if self._risk_service is None:
            self._risk_service = RiskEngineService()
        return self._risk_service

    @property
    def forecaster(self):
        if self._forecaster is None:
            self._forecaster = RainfallForecaster()
        return self._forecaster

    @property
    def weather_provider(self):
        if self._weather_provider is None:
            self._weather_provider = IMDWeatherProvider()
        return self._weather_provider
        
    async def get_alert(self, location_id: int) -> Dict[str, Any]:
        
        # 1. Weather
        weather = await self.weather_provider.get_current_weather(17.7, 83.3) 
        
        # 2. Risk (ML-based)
        risk = self.risk_service.calculate_risk(location_id, {"amount": 25.0, "timestamp": datetime.now(timezone.utc)})
        
        # 3. Forecast
        forecast = self.forecaster.forecast(25.0, 10.0, 15.0) 
        
        # 4. Satellite (Historical)
        try:
            get_raster_metadata("data/processed/feature04/validated_flood_label.tif")
            sat_state = "HISTORICAL"
        except:
            sat_state = "UNAVAILABLE"

        # Deterministic Scoring
        score = risk.risk_score
        if forecast["forecasted_rainfall"] > 50:
            score += 15
        
        # Logic to map score to level
        if score > 80:
            level = "SEVERE"
            reason = "High risk indicated by ML model and forecasted rainfall."
            action = "Follow official emergency guidance and avoid unnecessary travel."
        elif score > 60:
            level = "WARNING"
            reason = "Elevated risk indicated by current conditions."
            action = "Prepare for possible flooding and monitor official warnings."
        elif score > 40:
            level = "WATCH"
            reason = "Potential risk indicated by current conditions."
            action = "Monitor rainfall and local conditions."
        else:
            level = "NORMAL"
            reason = "No significant risk detected."
            action = "Continue normal monitoring."
            
        # Data State Aggregation
        states = [weather["data_state"], risk.data_state, "AVAILABLE", sat_state]
        if "ERROR" in states:
            data_state = "ERROR"
        elif "UNAVAILABLE" in states:
            data_state = "PARTIAL"
        else:
            data_state = "LIVE"

        return {
            "location_id": location_id,
            "alert_level": level,
            "risk_score": min(score, 100),
            "data_state": data_state,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "primary_reason": reason,
            "recommended_action": action,
            "contributing_factors": [
                {"name": "Current Weather", "source": weather["source"], "data_state": weather["data_state"]},
                {"name": "Rainfall Risk", "source": "ML_Risk_Engine", "data_state": risk.data_state},
                {"name": "Forecast", "source": "Rainfall_Forecaster", "data_state": "AVAILABLE"},
                {"name": "Historical Satellite", "source": "Copernicus_GFM", "data_state": sat_state}
            ]
        }
