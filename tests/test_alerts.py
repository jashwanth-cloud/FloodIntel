import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from unittest.mock import AsyncMock, patch

client = TestClient(app)

@pytest.mark.asyncio
async def test_get_alert_success():
    with patch("backend.app.services.alert_service.AlertEngineService.get_alert", new_callable=AsyncMock) as mock_get_alert:
        mock_get_alert.return_value = {
            "location_id": 1,
            "alert_level": "WATCH",
            "risk_score": 50,
            "data_state": "PARTIAL",
            "generated_at": "2026-09-09T00:00:00Z",
            "primary_reason": "Test reason",
            "recommended_action": "Test action",
            "contributing_factors": [],
            "source_summary": []
        }
        
        response = client.get("/api/v1/alerts/1")
        assert response.status_code == 200
        data = response.json()
        assert data["alert_level"] == "WATCH"
        assert data["risk_score"] == 50
