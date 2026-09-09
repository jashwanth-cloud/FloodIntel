import pytest
import asyncio
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.services.providers.weather_provider import IMDWeatherProvider

@pytest.mark.asyncio
async def test_weather_provider_live_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"temp": 30.0, "weather": "Sunny"}
    mock_response.raise_for_status = MagicMock()
    
    with patch("backend.app.services.providers.weather_provider.httpx.AsyncClient") as mock_client_class:
        # Properly configure the async context manager
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        # Make the context manager return the mock_client
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        
        provider = IMDWeatherProvider()
        provider.enabled = True
        
        result = await provider.get_current_weather(17.7, 83.3)
        assert result["data_state"] == "LIVE"
        assert result["temperature"] == 30.0
        assert mock_client.get.called

@pytest.mark.asyncio
async def test_weather_provider_cache_hit():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"temp": 30.0, "weather": "Sunny"}
    mock_response.raise_for_status = MagicMock()
    
    with patch("backend.app.services.providers.weather_provider.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        
        provider = IMDWeatherProvider()
        provider.enabled = True
        
        # First call
        await provider.get_current_weather(17.7, 83.3)
        # Second call
        await provider.get_current_weather(17.7, 83.3)
        
        assert mock_client.get.call_count == 1

@pytest.mark.asyncio
async def test_weather_provider_fallback_disabled():
    provider = IMDWeatherProvider()
    provider.enabled = False
    
    result = await provider.get_current_weather(17.7, 83.3)
    assert result["data_state"] == "UNAVAILABLE"
    assert result["source"] == "IMD_DEMO"
