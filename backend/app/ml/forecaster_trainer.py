import xarray as xr
import glob
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import json
from datetime import datetime

class RainfallForecasterTrainer:
    def __init__(self, data_dir="../data/raw/rainfall", model_dir="../models/rainfall_forecasting/random_forest/v1"):
        self.data_dir = data_dir
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)

    def prepare_data(self):
        files = sorted(glob.glob(os.path.join(self.data_dir, "*.nc")))
        dfs = []
        for file in files:
            ds = xr.open_dataset(file)
            df = ds['RAINFALL'].to_dataframe().reset_index()
            # Feature Engineering at time T
            df['lag_1'] = df.groupby(['LATITUDE', 'LONGITUDE'])['RAINFALL'].shift(1)
            df['rolling_mean_3'] = df.groupby(['LATITUDE', 'LONGITUDE'])['RAINFALL'].transform(lambda x: x.rolling(3).mean())
            
            # Target at time T+1 (Regression)
            df['target'] = df.groupby(['LATITUDE', 'LONGITUDE'])['RAINFALL'].shift(-1)
            
            df = df.dropna()
            dfs.append(df)
            ds.close()
            
        return pd.concat(dfs)

    def train(self):
        df = self.prepare_data()

        # Strict Chronological Split (subset for demonstration)
        train_df = df[(df['TIME'].dt.year >= 2021) & (df['TIME'].dt.year <= 2022)]
        
        X_train = train_df[['RAINFALL', 'lag_1', 'rolling_mean_3']]
        y_train = train_df['target']
        
        print(f"Training samples: {len(X_train)}")
        
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)
        
        # Save model
        joblib.dump(model, os.path.join(self.model_dir, "model.pkl"))
        
        # Save metadata
        metadata = {
            "model_version": "v1",
            "train_years": "2018-2022",
            "target": "RAINFALL(T+1)",
            "training_timestamp": datetime.now().isoformat()
        }
        with open(os.path.join(self.model_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)
            
        print("Forecasting training complete.")
        return model

if __name__ == "__main__":
    trainer = RainfallForecasterTrainer()
    trainer.train()
