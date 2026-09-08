import joblib
import pandas as pd
import os
import json
import xarray as xr
from datetime import datetime

class HeavyRainfallInference:
    def __init__(self, model_dir="../models/heavy_rainfall/random_forest/v2"):
        self.model = joblib.load(os.path.join(model_dir, "model.pkl"))
        with open(os.path.join(model_dir, "metadata.json"), "r") as f:
            self.metadata = json.load(f)
        self.threshold = self.metadata["threshold"]

    def predict(self, rainfall, lag_1, rolling_mean_3):
        features = pd.DataFrame([[rainfall, lag_1, rolling_mean_3]], columns=['RAINFALL', 'lag_1', 'rolling_mean_3'])
        prob = self.model.predict_proba(features)[0, 1]
        prediction = prob >= self.threshold
        return {
            "heavy_rainfall_predicted": bool(prediction),
            "probability": float(prob),
            "threshold": float(self.threshold),
            "model_version": self.metadata["model_version"],
            "target_horizon": "next_day",
            "data_state": "HISTORICAL"
        }
