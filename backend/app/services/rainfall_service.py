import xarray as xr
import glob
import os
from abc import ABC, abstractmethod
from datetime import datetime

class DataUnavailableError(Exception):
    pass

class RainfallProvider(ABC):
    @abstractmethod
    def get_rainfall(self, lat: float, lon: float, timestamp: datetime):
        pass

class IMDHistoricalRainfallProvider(RainfallProvider):
    def __init__(self, data_dir: str = "../data/raw/rainfall"):
        self.data_dir = data_dir
        self.datasets = {}
        self._load_datasets()

    def _load_datasets(self):
        print(f"Loading datasets from {self.data_dir}")
        files = glob.glob(os.path.join(self.data_dir, "*.nc"))
        print(f"Found files: {files}")
        for file in files:
            ds = xr.open_dataset(file, decode_times=True)
            # Use TIME coordinate, extract year
            year = ds['TIME'].dt.year.values[0]
            print(f"Loaded {year} from {file}")
            self.datasets[year] = ds

    def get_rainfall(self, lat: float, lon: float, timestamp: datetime):
        year = timestamp.year
        if year not in self.datasets:
            raise DataUnavailableError(f"No data for year {year}")
        
        ds = self.datasets[year]
        # Nearest neighbor extraction using correct coordinate names
        val = ds.sel(LATITUDE=lat, LONGITUDE=lon, TIME=timestamp, method="nearest")
        return {
            "amount": float(val.RAINFALL.values),
            "source": "IMD",
            "data_state": "HISTORICAL",
            "timestamp": timestamp.isoformat()
        }

class DemoRainfallProvider(RainfallProvider):
    def get_rainfall(self, lat: float, lon: float, timestamp: datetime):
        # Demo data: rainfall in mm
        return {
            "amount": 42.5,
            "source": "DEMO_SIMULATION",
            "data_state": "DEMO",
            "timestamp": timestamp.isoformat()
        }
