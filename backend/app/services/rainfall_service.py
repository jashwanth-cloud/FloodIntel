from abc import ABC, abstractmethod

class DataUnavailableError(Exception):
    pass

class RainfallProvider(ABC):
    @abstractmethod
    def get_latest_rainfall(self, location_id: int):
        pass

class IMDHistoricalRainfallProvider(RainfallProvider):
    def get_latest_rainfall(self, location_id: int):
        # Data not found
        raise DataUnavailableError("IMD historical rainfall data not found in repository.")

class DemoRainfallProvider(RainfallProvider):
    def get_latest_rainfall(self, location_id: int):
        # Demo data: rainfall in mm
        return {
            "amount": 42.5,
            "source": "DEMO_SIMULATION",
            "data_state": "DEMO",
            "timestamp": "2026-09-08T10:00:00Z"
        }
