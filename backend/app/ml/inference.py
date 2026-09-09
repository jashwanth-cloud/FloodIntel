import joblib
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

class HeavyRainfallInference:
    def __init__(self, model_dir=None):
        if model_dir is None:
            # Resolve path relative to this file: backend/app/ml/inference.py
            # Path to repo root: ../../../
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            model_dir = project_root / "models" / "heavy_rainfall" / "random_forest" / "v2"
        else:
            model_dir = Path(model_dir)

        self.model = joblib.load(model_dir / "model.pkl")
        with open(model_dir / "metadata.json", "r") as f:
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
