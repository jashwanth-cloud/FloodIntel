from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "flood_random_forest_model.joblib"
)


# IMPORTANT:
# feature_names_in_ is not stored in the existing model.
# Therefore this order is permanently locked to the training dataset.
MODEL_FEATURE_NAMES = [
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


def get_model_metadata() -> dict[str, Any]:
    """Return metadata for the trained Random Forest model."""

    if not MODEL_FILE.exists():
        return {
            "status": "unavailable",
            "model_file": str(MODEL_FILE),
            "reason": "Model file not found.",
        }

    try:
        model = joblib.load(MODEL_FILE)
    except Exception as exc:
        return {
            "status": "error",
            "model_file": str(MODEL_FILE),
            "reason": f"Unable to load model: {exc}",
        }

    feature_count = getattr(model, "n_features_in_", None)
    classes = getattr(model, "classes_", None)
    estimators = getattr(model, "n_estimators", None)

    if feature_count != len(MODEL_FEATURE_NAMES):
        return {
            "status": "error",
            "model_file": str(MODEL_FILE),
            "reason": (
                f"Expected {len(MODEL_FEATURE_NAMES)} features, "
                f"but model reports {feature_count}."
            ),
        }

    return {
        "status": "available",
        "model_type": type(model).__name__,
        "estimators": estimators,
        "feature_count": feature_count,
        "feature_names": MODEL_FEATURE_NAMES,
        "classes": (
            classes.tolist()
            if hasattr(classes, "tolist")
            else classes
        ),
        "prediction_mode": "precomputed_raster",
        "note": (
            "The current trained model is used for the existing "
            "precomputed flood prediction workflow. "
            "It is not currently exposed as a nationwide live "
            "location-based forecasting endpoint."
        ),
    }