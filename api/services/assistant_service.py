from __future__ import annotations

from typing import Any

import requests

from api.services.flood_service import load_flood_summary


OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b"


SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "te": "Telugu",
    "ta": "Tamil",
    "kn": "Kannada",
    "ml": "Malayalam",
    "bn": "Bengali",
}


def get_ollama_status() -> dict[str, Any]:
    """Check whether the local Ollama service and model are available."""

    try:
        response = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=5,
        )
        response.raise_for_status()

        models = response.json().get("models", [])

        available_models = [
            model.get("name", "")
            for model in models
        ]

        model_available = any(
            name == OLLAMA_MODEL
            or name.startswith(f"{OLLAMA_MODEL}:")
            for name in available_models
        )

        return {
            "service": "available",
            "model": OLLAMA_MODEL,
            "model_available": model_available,
            "available_models": available_models,
        }

    except requests.RequestException as exc:
        return {
            "service": "unavailable",
            "model": OLLAMA_MODEL,
            "model_available": False,
            "reason": str(exc),
        }


def _build_flood_context() -> str:
    """Build a compact factual context for the AI assistant."""

    summary = load_flood_summary()

    prediction = summary.get("prediction", {})
    risk = summary.get("risk", {})
    area = summary.get("area", {})
    validation = summary.get("validation", {})

    risk_level = risk.get(
        "level",
        risk.get("risk_level", "Unknown"),
    )

    return f"""
FloodIntel verified current dataset context:

Risk level:
{risk_level}

Predicted flood pixels:
{prediction.get("flood_pixels", "Unavailable")}

Total analyzed pixels:
{prediction.get("total_pixels", "Unavailable")}

Predicted flood percentage:
{prediction.get("flood_percentage", "Unavailable")}%

Predicted flooded area:
{area.get("flooded_area_km2", "Unavailable")} km2

Total analyzed area:
{area.get("total_area_km2", "Unavailable")} km2

Validation IoU:
{validation.get("iou", "Unavailable")}

Validation Dice:
{validation.get("dice", "Unavailable")}

Important scope limitation:
This is a precomputed satellite-event flood prediction result.
It is NOT a live nationwide flood forecast.
The current backend does not provide verified live rainfall,
live government alerts, nationwide future forecasts, or
location-specific real-time predictions.
"""


def ask_assistant(
    message: str,
    language: str = "en",
) -> dict[str, Any]:
    """Ask the local Ollama model using grounded FloodIntel context."""

    language = language.lower().strip()

    if language not in SUPPORTED_LANGUAGES:
        language = "en"

    language_name = SUPPORTED_LANGUAGES[language]

    status = get_ollama_status()

    if status["service"] != "available":
        return {
            "status": "unavailable",
            "message": (
                "FloodIntel AI Assistant is currently unavailable "
                "because the local AI service is not running."
            ),
            "model": OLLAMA_MODEL,
        }

    if not status["model_available"]:
        return {
            "status": "unavailable",
            "message": (
                f"The FloodIntel AI model '{OLLAMA_MODEL}' "
                "is not available in Ollama."
            ),
            "model": OLLAMA_MODEL,
        }

    flood_context = _build_flood_context()

    system_prompt = f"""
You are Lucky, the FloodIntel AI Assistant.

You are a safety-focused flood intelligence assistant.

Respond in {language_name}.

Use ONLY the verified FloodIntel context supplied below
for claims about the current flood prediction.

Never invent:
- live rainfall values
- live weather conditions
- government alerts
- flood locations
- future forecasts
- sensor readings
- evacuation orders
- model accuracy numbers not supplied in the context

If the user asks for information that FloodIntel does not
currently have, clearly say that the information is unavailable.

You may provide general flood-safety advice, but clearly
distinguish general safety guidance from verified FloodIntel data.

Do not present a precomputed event prediction as a live
nationwide prediction.

Keep responses concise, useful, and easy for citizens to understand.

Use "km2" when referring to square kilometres.
Do not use the "km²" symbol.

VERIFIED FLOODINTEL CONTEXT:
{flood_context}
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": message,
        "system": system_prompt,
        "stream": False,
    }

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=120,
        )

        response.raise_for_status()

        result = response.json()

        answer = result.get("response", "").strip()

        # Normalize incorrect square-kilometre encoding.
        answer = answer.replace("kmÂ²", "km2")
        answer = answer.replace("km²", "km2")

        if not answer:
            return {
                "status": "error",
                "message": "The AI model returned an empty response.",
                "model": OLLAMA_MODEL,
            }

        return {
            "status": "success",
            "message": answer,
            "language": language,
            "language_name": language_name,
            "model": OLLAMA_MODEL,
            "grounded": True,
        }

    except requests.Timeout:
        return {
            "status": "error",
            "message": "The AI assistant timed out. Please try again.",
            "model": OLLAMA_MODEL,
        }

    except requests.RequestException as exc:
        return {
            "status": "error",
            "message": f"AI service request failed: {exc}",
            "model": OLLAMA_MODEL,
        }