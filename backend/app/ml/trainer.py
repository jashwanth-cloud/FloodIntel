import xarray as xr
import glob
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import joblib
import json
from datetime import datetime

class HeavyRainfallTrainer:
    def __init__(self, data_dir="../data/raw/rainfall", model_dir="../models/heavy_rainfall/random_forest/v2"):
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
            
            # Target at time T+1
            df['target'] = df.groupby(['LATITUDE', 'LONGITUDE'])['RAINFALL'].shift(-1)
            df['target'] = (df['target'] >= 50).astype(int)
            
            df = df.dropna()
            dfs.append(df)
            ds.close()
            
        return pd.concat(dfs)

    def train(self):
        df = self.prepare_data()
        
        # Limit to 2018-2020 to speed up
        df = df[df['TIME'].dt.year <= 2020]

        # Chronological Split
        train_df = df[df['TIME'].dt.year <= 2019]
        val_df = df[df['TIME'].dt.year == 2020]
        
        X_train = train_df[['RAINFALL', 'lag_1', 'rolling_mean_3']]
        y_train = train_df['target']
        
        print(f"Training samples: {len(X_train)}")
        print(f"Positive samples: {y_train.sum()}")
        
        model = RandomForestClassifier(n_estimators=20, class_weight='balanced', random_state=42)
        model.fit(X_train, y_train)
        
        # Save model
        joblib.dump(model, os.path.join(self.model_dir, "model.pkl"))
        
        # Evaluate
        y_pred = model.predict(train_df[['RAINFALL', 'lag_1', 'rolling_mean_3']])
        metrics = classification_report(y_train, y_pred, output_dict=True)
        
        # Save metadata
        metadata = {
            "model_version": "v2",
            "train_years": "2018-2022",
            "threshold": 50,
            "metrics": metrics,
            "training_timestamp": datetime.now().isoformat()
        }
        with open(os.path.join(self.model_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)
            
        print("Training complete. Artifacts saved.")
        return model

if __name__ == "__main__":
    trainer = HeavyRainfallTrainer()
    trainer.train()
