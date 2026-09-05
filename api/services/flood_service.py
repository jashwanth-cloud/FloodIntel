import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SUMMARY_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "flood_prediction_summary.json"
)


def load_flood_summary() -> dict:
    """Load the precomputed flood prediction summary."""

    if not SUMMARY_FILE.exists():
        raise FileNotFoundError(
            f"Flood prediction summary not found: {SUMMARY_FILE}"
        )

    try:
        with SUMMARY_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in flood prediction summary: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError("Flood prediction summary must contain a JSON object.")

    return data


def get_flood_status() -> dict:
    """Return the flood prediction data for the API."""

    summary = load_flood_summary()

    return {
        "status": "success",
        "data": summary,
    }