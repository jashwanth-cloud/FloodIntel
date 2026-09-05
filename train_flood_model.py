import os
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
)


DATASET_FILE = r"data\processed\flood_training_dataset.csv"

MODEL_FILE = r"data\processed\flood_random_forest_model.joblib"

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


print("=" * 70)
print("SENTINEL-1 FLOOD CLASSIFICATION MODEL TRAINING")
print("=" * 70)


# ------------------------------------------------------------------
# LOAD DATASET
# ------------------------------------------------------------------

print()
print("Dataset:")
print(DATASET_FILE)

print()
print("Loading training dataset...")

df = pd.read_csv(DATASET_FILE)

print("Rows:", len(df))
print("Columns:", len(df.columns))


# ------------------------------------------------------------------
# VALIDATE DATASET
# ------------------------------------------------------------------

print()
print("Validating dataset...")

required_columns = FEATURE_NAMES + ["flood_label"]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing columns: {missing_columns}"
    )

print("Required columns: OK")


# ------------------------------------------------------------------
# PREPARE X AND Y
# ------------------------------------------------------------------

X = df[FEATURE_NAMES].values

y = df["flood_label"].values


print()
print("Feature matrix:", X.shape)
print("Label vector:", y.shape)


# ------------------------------------------------------------------
# CLASS DISTRIBUTION
# ------------------------------------------------------------------

print()
print("Original class distribution:")

unique, counts = np.unique(
    y,
    return_counts=True,
)

for label, count in zip(unique, counts):

    print(
        "Class:",
        int(label),
        "Pixels:",
        int(count),
        "Percent:",
        round(
            float(count) / len(y) * 100,
            4,
        ),
    )


# ------------------------------------------------------------------
# TRAIN / TEST SPLIT
# ------------------------------------------------------------------

print()
print("Creating stratified train/test split...")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

print("Training samples:", len(y_train))
print("Testing samples :", len(y_test))


# ------------------------------------------------------------------
# TRAIN RANDOM FOREST
# ------------------------------------------------------------------

print()
print("Training Random Forest...")

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=None,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)


model.fit(
    X_train,
    y_train,
)

print("Model training complete.")


# ------------------------------------------------------------------
# PREDICTION
# ------------------------------------------------------------------

print()
print("Running test predictions...")

y_pred = model.predict(X_test)

y_probability = model.predict_proba(X_test)[:, 1]


# ------------------------------------------------------------------
# METRICS
# ------------------------------------------------------------------

print()
print("=" * 70)
print("MODEL EVALUATION")
print("=" * 70)


accuracy = model.score(
    X_test,
    y_test,
)

precision = precision_score(
    y_test,
    y_pred,
    zero_division=0,
)

recall = recall_score(
    y_test,
    y_pred,
    zero_division=0,
)

f1 = f1_score(
    y_test,
    y_pred,
    zero_division=0,
)

roc_auc = roc_auc_score(
    y_test,
    y_probability,
)

pr_auc = average_precision_score(
    y_test,
    y_probability,
)


print()
print("Accuracy :", round(accuracy, 6))
print("Precision:", round(precision, 6))
print("Recall   :", round(recall, 6))
print("F1 Score :", round(f1, 6))
print("ROC-AUC  :", round(roc_auc, 6))
print("PR-AUC   :", round(pr_auc, 6))


# ------------------------------------------------------------------
# CLASSIFICATION REPORT
# ------------------------------------------------------------------

print()
print("=" * 70)
print("CLASSIFICATION REPORT")
print("=" * 70)

print()

print(
    classification_report(
        y_test,
        y_pred,
        target_names=[
            "Non-Flood",
            "Flood",
        ],
        digits=4,
        zero_division=0,
    )
)


# ------------------------------------------------------------------
# CONFUSION MATRIX
# ------------------------------------------------------------------

print("=" * 70)
print("CONFUSION MATRIX")
print("=" * 70)

cm = confusion_matrix(
    y_test,
    y_pred,
)

print()

print("                 Predicted")
print("                 Non-Flood   Flood")
print()
print(
    f"Actual Non-Flood  {cm[0,0]:8d}  {cm[0,1]:7d}"
)
print(
    f"Actual Flood      {cm[1,0]:8d}  {cm[1,1]:7d}"
)


# ------------------------------------------------------------------
# FEATURE IMPORTANCE
# ------------------------------------------------------------------

print()
print("=" * 70)
print("FEATURE IMPORTANCE")
print("=" * 70)

importance = model.feature_importances_

feature_importance = (
    pd.DataFrame(
        {
            "feature": FEATURE_NAMES,
            "importance": importance,
        }
    )
    .sort_values(
        "importance",
        ascending=False,
    )
)


print()

for _, row in feature_importance.iterrows():

    print(
        f"{row['feature']:<25}"
        f"{row['importance']:.6f}"
    )


# ------------------------------------------------------------------
# SAVE MODEL
# ------------------------------------------------------------------

print()
print("Saving model...")

os.makedirs(
    os.path.dirname(MODEL_FILE),
    exist_ok=True,
)

joblib.dump(
    model,
    MODEL_FILE,
)


# ------------------------------------------------------------------
# FINAL SUMMARY
# ------------------------------------------------------------------

print()
print("=" * 70)
print("FLOOD MODEL TRAINING COMPLETE")
print("=" * 70)

print()
print("Model:", MODEL_FILE)

print()
print("Evaluation metrics:")

print("Accuracy :", round(accuracy, 6))
print("Precision:", round(precision, 6))
print("Recall   :", round(recall, 6))
print("F1 Score :", round(f1, 6))
print("ROC-AUC  :", round(roc_auc, 6))
print("PR-AUC   :", round(pr_auc, 6))

print()
print("Next stage:")
print("Generate a full 512 x 512 flood prediction raster.")

print()
print("=" * 70)