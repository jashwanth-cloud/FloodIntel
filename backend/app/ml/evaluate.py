import xarray as xr
import glob
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, average_precision_score
import joblib
import json

class Evaluator:
    def __init__(self, data_dir="../data/raw/rainfall", model_dir="../models/heavy_rainfall/random_forest/v2"):
        self.data_dir = data_dir
        self.model_dir = model_dir
        self.model = joblib.load(os.path.join(model_dir, "model.pkl"))
        with open(os.path.join(model_dir, "metadata.json"), "r") as f:
            self.metadata = json.load(f)
        self.threshold = self.metadata["threshold"]

    def prepare_data(self):
        # Optimized to load only needed files based on logic in evaluate()
        files = sorted(glob.glob(os.path.join(self.data_dir, "*.nc")))
        # Load only 2023 and 2025 files
        target_files = [f for f in files if "2023" in f or "2025" in f]
        dfs = []
        for file in target_files:
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

    def evaluate(self):
        df = self.prepare_data()
        val_df = df[df['TIME'].dt.year == 2023]
        test_df = df[df['TIME'].dt.year == 2025]
        
        # Validation
        X_val = val_df[['RAINFALL', 'lag_1', 'rolling_mean_3']]
        y_val = val_df['target']
        probs_val = self.model.predict_proba(X_val)[:, 1]
        
        val_roc_auc = roc_auc_score(y_val, probs_val)
        val_pr_auc = average_precision_score(y_val, probs_val)
        
        # Test
        X_test = test_df[['RAINFALL', 'lag_1', 'rolling_mean_3']]
        y_test = test_df['target']
        probs_test = self.model.predict_proba(X_test)[:, 1]
        
        test_roc_auc = roc_auc_score(y_test, probs_test)
        test_pr_auc = average_precision_score(y_test, probs_test)
        
        # Update metadata
        self.metadata["val_metrics"]["roc_auc"] = val_roc_auc
        self.metadata["val_metrics"]["pr_auc"] = val_pr_auc
        self.metadata["test_metrics"]["roc_auc"] = test_roc_auc
        self.metadata["test_metrics"]["pr_auc"] = test_pr_auc
        
        with open(os.path.join(self.model_dir, "metadata.json"), "w") as f:
            json.dump(self.metadata, f, indent=4)
        
        print("Metrics updated.")
        print(f"Val ROC-AUC: {val_roc_auc}, PR-AUC: {val_pr_auc}")
        print(f"Test ROC-AUC: {test_roc_auc}, PR-AUC: {test_pr_auc}")

if __name__ == "__main__":
    evaluator = Evaluator()
    evaluator.evaluate()
