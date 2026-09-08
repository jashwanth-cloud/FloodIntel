import joblib
import pandas as pd
import os
import json

class HeavyRainfallInference:
    def __init__(self, model_dir="../models/heavy_rainfall/random_forest/v2"):
        self.model = joblib.load(os.path.join(model_dir, "model.pkl"))
        with open(os.path.join(model_dir, "metadata.json"), "r") as f:
            self.metadata = json.load(f)

    def predict(self, rainfall, lag_1, rolling_mean_3):
        features = pd.DataFrame([[rainfall, lag_1, rolling_mean_3]], columns=['RAINFALL', 'lag_1', 'rolling_mean_3'])
        prediction = self.model.predict(features)
        return {
            "heavy_rainfall_detected": bool(prediction[0]),
            "model_version": self.metadata["model_version"],
            "data_state": "HISTORICAL"
        }
