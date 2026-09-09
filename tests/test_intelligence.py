import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from unittest.mock import AsyncMock, patch

client = TestClient(app)

@pytest.mark.asyncio
async def test_get_intelligence_success():
    with patch("backend.app.services.ai.grounded_intelligence_service.GroundedIntelligenceService.get_intelligence", new_callable=AsyncMock) as mock_get_intel:
        mock_get_intel.return_value = {
            "summary": "AI Intelligence test summary",
            "severity": "NORMAL",
            "key_findings": ["Test finding"],
            "reasoning": ["Test reasoning"],
            "recommended_actions": ["Test action"],
            "data_state": "LIVE",
            "sources": ["Test source"],
            "limitations": ["Test limitation"],
            "uncertainty": []
        }
        
        response = client.get("/api/v1/intelligence/1")
        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == "AI Intelligence test summary"
        assert data["severity"] == "NORMAL"
