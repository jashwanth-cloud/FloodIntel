import os
import time
import httpx
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class WeatherProvider(ABC):
    @abstractmethod
    async def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        pass

class IMDWeatherProvider(WeatherProvider):
    def __init__(self):
        self.base_url = os.getenv("IMD_API_BASE_URL")
        self.api_key = os.getenv("IMD_API_KEY")
        self.enabled = os.getenv("IMD_API_ENABLED") == "true"
        self.timeout = int(os.getenv("IMD_API_TIMEOUT", 10))
        self.ttl = int(os.getenv("IMD_CACHE_TTL", 300))
        
        self.cache = {}
        self.cache_time = {}

    async def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        if not self.enabled:
            return self._demo_response(lat, lon, "UNAVAILABLE")

        cache_key = f"{lat}_{lon}"
        if cache_key in self.cache and (time.time() - self.cache_time.get(cache_key, 0) < self.ttl):
            return self.cache[cache_key]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Placeholder for actual endpoint construction based on IMD docs
                # e.g., /current_weather?lat={lat}&lon={lon}
                response = await client.get(f"{self.base_url}/current_weather", params={"lat": lat, "lon": lon, "key": self.api_key})
                response.raise_for_status()
                data = response.json()
                
                # Normalize response
                result = {
                    "source": "IMD",
                    "data_state": "LIVE",
                    "temperature": data.get("temp"),
                    "weather_condition": data.get("condition"),
                    "fetched_at": time.time()
                }
                self.cache[cache_key] = result
                self.cache_time[cache_key] = time.time()
                return result
        except Exception as e:
            print(f"IMD API failed: {e}")
            return self._demo_response(lat, lon, "ERROR")

    def _demo_response(self, lat, lon, state):
        return {
            "source": "DEMO_FALLBACK",
            "data_state": state,
            "temperature": 28.5,
            "weather_condition": "Partly Cloudy",
            "fetched_at": time.time()
        }
