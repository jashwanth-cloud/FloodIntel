import pytest
from datetime import datetime, timezone
from unittest.mock import patch
from backend.app.services.risk_engine_service import RiskEngineService

def test_calculate_risk_execution_and_serialization():
    # Mock ML inference to avoid model loading issues in tests
    with patch("backend.app.services.risk_engine_service.HeavyRainfallInference") as mock_inference:
        mock_inference.return_value.predict.return_value = {
            "heavy_rainfall_predicted": False,
            "probability": 0.1,
            "threshold": 0.5,
            "model_version": "test-v1"
        }
        
        service = RiskEngineService()
        
        # Test case: input datetime as timestamp
        test_ts = datetime(2026, 9, 9, 12, 0, 0, tzinfo=timezone.utc)
        rainfall_data = {
            "amount": 10.0,
            "timestamp": test_ts,
            "data_state": "HISTORICAL"
        }
        
        assessment = service.calculate_risk(1, rainfall_data)
        
        # Verify timestamp serialization
        assert isinstance(assessment.timestamp, str)
        assert assessment.timestamp == test_ts.isoformat()
        assert assessment.location_id == 1
        assert assessment.risk_level == "LOW"
