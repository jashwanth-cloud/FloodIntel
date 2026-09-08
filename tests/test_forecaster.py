import pytest
from backend.app.ml.forecaster import RainfallForecaster
import numpy as np

def test_forecaster_inference():
    forecaster = RainfallForecaster()
    result = forecaster.forecast(rainfall=50.0, lag_1=40.0, rolling_mean_3=45.0)
    assert "forecasted_rainfall" in result
    assert result["model_version"] == "v1"
    assert result["data_state"] == "HISTORICAL"
    assert isinstance(result["forecasted_rainfall"], float)
