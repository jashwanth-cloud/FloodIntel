import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
import os

client = TestClient(app)

# Assuming the raster file exists in the relative path from the project root
# If running tests from the project root, path should be correct
RASTER_PATH = "data/processed/feature04/validated_flood_label.tif"

def test_get_satellite_flood_success():
    if not os.path.exists(RASTER_PATH):
        pytest.skip("Satellite data not found, skipping test")
    
    response = client.get("/api/v1/satellite/flood/default")
    assert response.status_code == 200
    data = response.json()
    assert data["location_id"] == "default"
    assert data["data_state"] == "HISTORICAL"
    assert "crs" in data
    assert "flooded_area_sqm" in data

def test_get_satellite_flood_invalid_location():
    response = client.get("/api/v1/satellite/flood/nonexistent")
    assert response.status_code == 404

def test_get_satellite_flood_metadata_structure():
    if not os.path.exists(RASTER_PATH):
        pytest.skip("Satellite data not found, skipping test")

    response = client.get("/api/v1/satellite/flood/default")
    data = response.json()
    assert "event_id" in data
    assert "source" in data
    assert "provenance" in data
    assert "observation_type" in data
    assert data["observation_type"] == "SATELLITE_OBSERVED"
