import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import classification_report

DATASET_FILE = r"data\processed\flood_training_dataset.csv"

FEATURE_NAMES = [
    "before_vv",
    "before_vh",
    "after_vv",
    "after_vh",
    "vv_change",
    "vh_change",
    "vv_ratio",
    "vh_ratio",
    "before_vv_vh_ratio",
    "after_vv_vh_ratio",
    "vv_vh_change",
]

def main():
    print("=" * 70)
    print("ML PIPELINE VALIDATION & CROSS-VALIDATION")
    print("=" * 70)

    if not os.path.exists(DATASET_FILE):
        print(f"Error: Dataset file not found at {DATASET_FILE}")
        return

    print(f"Loading dataset from: {DATASET_FILE}")
    df = pd.read_csv(DATASET_FILE)
    print(f"Loaded {len(df)} rows and {len(df.columns)} columns.")

    # 1. Check feature correlation
    print("\n" + "-" * 70)
    print("1. FEATURE CORRELATION ANALYSIS")
    print("-" * 70)
    
    corr_matrix = df[FEATURE_NAMES].corr()
    print("\nFeature correlation matrix:")
    print(corr_matrix.round(3))

    # Identify highly correlated features (> 0.90 or < -0.90)
    print("\nHighly correlated pairs (> 0.90 or < -0.90):")
    pairs_found = False
    for i in range(len(corr_matrix.columns)):
        for j in range(i):
            if abs(corr_matrix.iloc[i, j]) > 0.90:
                print(f"  * {corr_matrix.columns[i]} <-> {corr_matrix.columns[j]}: {corr_matrix.iloc[i, j]:.3f}")
                pairs_found = True
    if not pairs_found:
        print("  None found.")

    # 2. Stratified Cross-Validation
    print("\n" + "-" * 70)
    print("2. STRATIFIED CROSS-VALIDATION (5-FOLD)")
    print("-" * 70)
    
    X = df[FEATURE_NAMES].values
    y = df["flood_label"].values

    # To run validation quickly while maintaining statistical significance,
    # we take a 20% stratified sample of the data.
    from sklearn.model_selection import train_test_split
    _, X_sample, _, y_sample = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )
    print(f"Using a 20% stratified sample for validation: {len(y_sample)} pixels")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    model = RandomForestClassifier(
        n_estimators=100,  # 100 trees is sufficient for validation check
        max_depth=None,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    scoring = ['accuracy', 'precision', 'recall', 'f1']
    print("Running cross-validation...")
    scores = cross_validate(model, X_sample, y_sample, cv=cv, scoring=scoring, n_jobs=-1)

    print("\nCross-validation results (Mean ± Std):")
    print(f"  Accuracy : {scores['test_accuracy'].mean():.4f} ± {scores['test_accuracy'].std():.4f}")
    print(f"  Precision: {scores['test_precision'].mean():.4f} ± {scores['test_precision'].std():.4f}")
    print(f"  Recall   : {scores['test_recall'].mean():.4f} ± {scores['test_recall'].std():.4f}")
    print(f"  F1 Score : {scores['test_f1'].mean():.4f} ± {scores['test_f1'].std():.4f}")

    print("\n" + "=" * 70)
    print("ML PIPELINE VALIDATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
