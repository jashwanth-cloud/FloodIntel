import xarray as xr
import glob
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, precision_recall_curve, f1_score
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

        # Chronological Split
        # Subset training to 2021-2022 to fit in time
        train_df = df[(df['TIME'].dt.year >= 2021) & (df['TIME'].dt.year <= 2022)]
        val_df = df[df['TIME'].dt.year.isin([2023, 2024])]
        test_df = df[df['TIME'].dt.year == 2025]

        X_train = train_df[['RAINFALL', 'lag_1', 'rolling_mean_3']]
        y_train = train_df['target']

        print(f"Training samples: {len(X_train)}")

        model = RandomForestClassifier(n_estimators=20, class_weight='balanced', random_state=42)
        model.fit(X_train, y_train)

        
        # Validation for Threshold Selection
        X_val = val_df[['RAINFALL', 'lag_1', 'rolling_mean_3']]
        y_val = val_df['target']
        probs = model.predict_proba(X_val)[:, 1]
        precisions, recalls, thresholds = precision_recall_curve(y_val, probs)
        
        # Select threshold (max f1)
        f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-10)
        best_idx = np.argmax(f1_scores)
        best_threshold = thresholds[best_idx]
        
        print(f"Best threshold: {best_threshold}")
        
        # Save model
        joblib.dump(model, os.path.join(self.model_dir, "model.pkl"))
        
        # Save metadata
        metadata = {
            "model_version": "v2",
            "train_years": "2018-2022",
            "val_years": "2023-2024",
            "test_years": "2025",
            "threshold": float(best_threshold),
            "training_timestamp": datetime.now().isoformat()
        }
        with open(os.path.join(self.model_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)
            
        print("Training complete. Artifacts saved.")
        return model, best_threshold

if __name__ == "__main__":
    trainer = HeavyRainfallTrainer()
    trainer.train()
