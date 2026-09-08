import joblib
import pandas as pd
import os
import json

class RainfallForecaster:
    def __init__(self, model_dir=None):
        if model_dir is None:
            # Assume run from project root
            model_dir = "models/rainfall_forecasting/random_forest/v1"
        self.model = joblib.load(os.path.join(model_dir, "model.pkl"))
        with open(os.path.join(model_dir, "metadata.json"), "r") as f:
            self.metadata = json.load(f)

    def forecast(self, rainfall, lag_1, rolling_mean_3):
        features = pd.DataFrame([[rainfall, lag_1, rolling_mean_3]], columns=['RAINFALL', 'lag_1', 'rolling_mean_3'])
        prediction = self.model.predict(features)
        return {
            "forecasted_rainfall": float(prediction[0]),
            "model_version": self.metadata["model_version"],
            "data_state": "HISTORICAL"
        }
