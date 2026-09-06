from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SUMMARY_FILE = PROJECT_ROOT / "data" / "processed" / "flood_prediction_summary.json"


def load_flood_summary() -> dict[str, Any]:
    if not SUMMARY_FILE.exists():
        raise FileNotFoundError(
            f"Flood prediction summary not found: {SUMMARY_FILE}"
        )

    try:
        with SUMMARY_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Flood prediction summary contains invalid JSON: {SUMMARY_FILE}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError("Flood prediction summary must contain a JSON object.")

    return data


def get_flood_status() -> dict[str, Any]:
    summary = load_flood_summary()

    prediction = summary.get("prediction", {})
    risk = summary.get("risk", {})
    area = summary.get("area", {})

    return {
        "status": "success",
        "data": {
            "prediction": prediction,
            "risk": risk,
            "area": area,
        },
        "source": "precomputed_flood_prediction",
    }


def get_flood_summary() -> dict[str, Any]:
    return {
        "status": "success",
        "data": load_flood_summary(),
        "source": "precomputed_flood_prediction",
    }


def get_flood_statistics() -> dict[str, Any]:
    summary = load_flood_summary()

    return {
        "status": "success",
        "statistics": summary.get(
            "statistics",
            summary.get("area", {}),
        ),
    }


def get_flood_validation() -> dict[str, Any]:
    summary = load_flood_summary()

    return {
        "status": "success",
        "validation": summary.get("validation", {}),
    }


def get_flood_advisory() -> dict[str, Any]:
    summary = load_flood_summary()

    prediction = summary.get("prediction", {})
    risk = summary.get("risk", {})

    risk_level = str(
        risk.get(
            "level",
            risk.get("risk_level", "Unknown"),
        )
    )

    normalized = risk_level.lower()

    if normalized == "high":
        advisory = (
            "High flood risk detected. Avoid low-lying and waterlogged "
            "areas and follow official emergency instructions."
        )
    elif normalized in {"medium", "moderate"}:
        advisory = (
            "Moderate flood risk detected. Stay alert and monitor "
            "rainfall and official alerts."
        )
    elif normalized == "low":
        advisory = (
            "Low flood risk indicated by the current prediction. "
            "Continue monitoring official alerts and local conditions."
        )
    else:
        advisory = (
            "The current prediction does not provide a clear risk level. "
            "Please monitor official emergency information."
        )

    return {
        "status": "success",
        "risk_level": risk_level,
        "prediction": prediction,
        "advisory": advisory,
    }


def get_flood_explanation() -> dict[str, Any]:
    summary = load_flood_summary()

    prediction = summary.get("prediction", {})
    risk = summary.get("risk", {})
    area = summary.get("area", {})
    validation = summary.get("validation", {})

    risk_level = str(
        risk.get(
            "level",
            risk.get("risk_level", "Unknown"),
        )
    )

    flood_pixels = prediction.get("flood_pixels")
    total_pixels = prediction.get("total_pixels")
    flood_percentage = prediction.get("flood_percentage")

    flooded_area = area.get("flooded_area_km2")
    total_area = area.get("total_area_km2")

    iou = validation.get("iou")
    dice = validation.get("dice")

    evidence: list[str] = []

    if flood_pixels is not None and total_pixels is not None:
        evidence.append(
            f"The current analyzed prediction classifies "
            f"{flood_pixels:,} of {total_pixels:,} pixels as flooded."
        )

    if flood_percentage is not None:
        evidence.append(
            f"Flood-classified pixels represent approximately "
            f"{float(flood_percentage):.2f}% of the analyzed raster."
        )

    if flooded_area is not None:
        evidence.append(
            f"The estimated flooded area in the analyzed raster is "
            f"{float(flooded_area):.2f} km2."
        )

    if total_area is not None:
        evidence.append(
            f"The analyzed raster covers approximately "
            f"{float(total_area):.2f} km2."
        )

    validation_metrics: dict[str, Any] = {}

    if iou is not None:
        validation_metrics["iou"] = iou

    if dice is not None:
        validation_metrics["dice"] = dice

    limitations = [
        "This is a precomputed satellite-event flood prediction result.",
        "It is not a live nationwide flood forecast.",
        "Live rainfall observations are not currently integrated into this endpoint.",
        "Live government emergency alerts are not currently integrated into this endpoint.",
        "Future location-specific flood forecasting is not currently exposed by this API.",
    ]

    return {
        "status": "success",
        "risk_level": risk_level,
        "evidence": evidence,
        "validation": validation_metrics,
        "limitations": limitations,
        "source": "precomputed_flood_prediction",
    }

